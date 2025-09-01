from fastapi import FastAPI, Request, Form, Depends, HTTPException, Query, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import socketio
from typing import List

from database import SessionLocal, get_db, Base, engine
from models import User, Message, Friend, Group, GroupMember

#  Database 
Base.metadata.create_all(bind=engine)

#  FastAPI + Socket.IO 
app = FastAPI()
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app.mount("/socket.io", socketio.ASGIApp(sio))
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

#  Timezone 
LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
def hms_local(dt):
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(LOCAL_TZ).strftime("%H:%M:%S")

templates.env.filters["hms_local"] = hms_local

#  Password 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#  Current user 
def get_current_user(request: Request):
    username = request.cookies.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username

#  Pages 
@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse("/login")

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username đã tồn tại"})
    user = User(username=username, password=pwd_context.hash(password))
    db.add(user)
    db.commit()
    return RedirectResponse("/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Username hoặc password sai"})
    resp = RedirectResponse("/chat", status_code=303)
    resp.set_cookie("username", username, httponly=True, max_age=3600)
    return resp


@app.get("/chat", response_class=HTMLResponse)
def chat_page(
    request: Request,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Lấy thông tin người dùng hiện tại
    me = db.query(User).filter(User.username == username).first()

    # Lấy 50 tin nhắn gần nhất
    messages = (
        db.query(Message)
        .options(joinedload(Message.sender), joinedload(Message.receiver), joinedload(Message.group))
        .order_by(Message.timestamp.asc())
        .limit(50)
        .all()
    )

    # Lấy danh sách bạn bè đã accept
    friends = db.query(Friend).filter(
        (Friend.status == "accepted") & ((Friend.user_id == me.id) | (Friend.friend_id == me.id))
    ).all()

    friend_users = []
    for f in friends:
        if f.friend_id == me.id:
            u = db.query(User).get(f.user_id)
        else:
            u = db.query(User).get(f.friend_id)
        friend_users.append(u)

    # Lấy danh sách group mà user tham gia
    groups = (
        db.query(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .filter(GroupMember.user_id == me.id)
        .all()
    )

    # Trả về template với tất cả dữ liệu
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "username": username,
        "user_id": me.id,
        "messages": messages,
        "users": friend_users,
        "groups": groups 
    })

#  Friend APIs 

# Tìm kiếm user theo username
@app.get("/users/search")
def search_users(q: str, db: Session = Depends(get_db), username: str = Depends(get_current_user)):
    me = db.query(User).filter(User.username == username).first()
    users = db.query(User).filter(User.username.ilike(f"%{q}%"), User.id != me.id).all()
    return [{"id": u.id, "username": u.username, "avatar": u.avatar} for u in users]

# Gửi lời mời kết bạn (đã có rồi ở trên)
@app.post("/friends/{friend_id}")
def add_friend(friend_id: int, db: Session = Depends(get_db), username: str = Depends(get_current_user)):
    me = db.query(User).filter(User.username == username).first()
    if me.id == friend_id:
        raise HTTPException(400, "Không thể kết bạn với chính mình")

    exists = db.query(Friend).filter(
        ((Friend.user_id == me.id) & (Friend.friend_id == friend_id)) |
        ((Friend.user_id == friend_id) & (Friend.friend_id == me.id))
    ).first()
    if exists:
        return {"status": "exists", "friend_id": friend_id}

    friend = Friend(user_id=me.id, friend_id=friend_id, status="pending")
    db.add(friend)
    db.commit()
    return {"status": "pending", "friend_id": friend_id}

# Chấp nhận lời mời
@app.post("/friends/accept/{request_id}")
def accept_friend(request_id: int, db: Session = Depends(get_db), username: str = Depends(get_current_user)):
    me = db.query(User).filter(User.username == username).first()
    req = db.query(Friend).filter(
        Friend.id == request_id,
        Friend.friend_id == me.id,
        Friend.status == "pending"
    ).first()
    if not req:
        raise HTTPException(404, "Không có lời mời hợp lệ")
    req.status = "accepted"
    db.commit()
    return {"message": "Đã chấp nhận"}

#  Lấy danh sách lời mời kết bạn 
@app.get("/friends/requests")
def get_friend_requests(db: Session = Depends(get_db), username: str = Depends(get_current_user)):
    me = db.query(User).filter(User.username == username).first()
    requests = db.query(Friend).filter(Friend.friend_id == me.id, Friend.status == "pending").all()
    result = []
    for r in requests:
        u = db.query(User).get(r.user_id)
        result.append({
            "request_id": r.id,
            "username": u.username,
            "user_id": u.id
        })
    return result

# Lấy danh sách bạn bè
@app.get("/friends")
def get_friends(db: Session = Depends(get_db), username: str = Depends(get_current_user)):
    me = db.query(User).filter(User.username == username).first()
    friends = db.query(Friend).filter(
        (Friend.status == "accepted") &
        ((Friend.user_id == me.id) | (Friend.friend_id == me.id))
    ).all()

    result = []
    for f in friends:
        if f.friend_id == me.id:
            u = db.query(User).get(f.user_id)
        else:
            u = db.query(User).get(f.friend_id)
        result.append({
            "id": u.id,
            "username": u.username,
            "avatar": u.avatar
        })
    return result
#  Group APIs 

@app.post("/groups/create_with_members")
async def create_group_with_members(
    name: str = Form(...),
    member_ids: str = Form(...),  # Nhận chuỗi JSON của array
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user)
):
    import json
    try:
        # Parse member_ids từ JSON string
        member_id_list = json.loads(member_ids)
        if not isinstance(member_id_list, list):
            raise HTTPException(400, "member_ids phải là một array")
        
        if len(member_id_list) == 0:
            raise HTTPException(400, "Phải chọn ít nhất 1 thành viên")
            
        me = db.query(User).filter(User.username == username).first()
        
        # Tạo nhóm
        group = Group(name=name, owner_id=me.id)
        db.add(group)
        db.commit()
        db.refresh(group)

        # Thêm creator (owner) vào nhóm
        db.add(GroupMember(group_id=group.id, user_id=me.id, role="owner"))

        # Thêm các thành viên được chọn
        for uid in member_id_list:
            uid = int(uid)  # Đảm bảo là số
            # Kiểm tra user tồn tại
            user_exists = db.query(User).filter(User.id == uid).first()
            if user_exists:
                db.add(GroupMember(group_id=group.id, user_id=uid, role="member"))

        db.commit()

        # Emit cho các thành viên mới để họ thấy nhóm
        all_member_ids = [me.id] + [int(uid) for uid in member_id_list]
        for uid in all_member_ids:
            await sio.emit("new_group", {
                "group_id": group.id, 
                "name": group.name
            }, room=f"user_{uid}")

        return {
            "group_id": group.id, 
            "name": group.name,
            "member_count": len(all_member_ids)
        }
        
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid member_ids format")
    except Exception as e:
        print(f"Error creating group: {e}")
        raise HTTPException(500, "Lỗi tạo nhóm")


@app.post("/groups/{group_id}/add_members")
async def add_members_to_group(
    group_id: int,
    member_ids: str = Form(...),  # JSON string của array user IDs
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user)
):
    import json
    try:
        # Parse member_ids từ JSON string  
        member_id_list = json.loads(member_ids)
        if not isinstance(member_id_list, list):
            raise HTTPException(400, "member_ids phải là một array")
            
        if len(member_id_list) == 0:
            raise HTTPException(400, "Phải chọn ít nhất 1 thành viên")

        me = db.query(User).filter(User.username == username).first()
        group = db.query(Group).filter(Group.id == group_id).first()
        
        if not group:
            raise HTTPException(404, "Nhóm không tồn tại")

        # Kiểm tra quyền (chỉ owner hoặc admin có thể thêm thành viên)
        my_membership = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == me.id
        ).first()
        
        if not my_membership or my_membership.role not in ["owner", "admin"]:
            raise HTTPException(403, "Bạn không có quyền thêm thành viên vào nhóm này")

        added_members = []
        for uid in member_id_list:
            uid = int(uid)
            
            # Kiểm tra user tồn tại
            user_exists = db.query(User).filter(User.id == uid).first()
            if not user_exists:
                continue
                
            # Kiểm tra đã là thành viên chưa
            existing_member = db.query(GroupMember).filter(
                GroupMember.group_id == group_id,
                GroupMember.user_id == uid
            ).first()
            
            if not existing_member:
                # Thêm thành viên mới
                db.add(GroupMember(group_id=group_id, user_id=uid, role="member"))
                added_members.append(uid)

        db.commit()

        # Emit cho các thành viên mới về việc được thêm vào nhóm
        for uid in added_members:
            await sio.emit("new_group", {
                "group_id": group.id,
                "name": group.name
            }, room=f"user_{uid}")
            
        # Emit cho các thành viên hiện tại về việc có thành viên mới
        existing_members = db.query(GroupMember).filter(
            GroupMember.group_id == group_id
        ).all()
        
        for member in existing_members:
            if member.user_id not in added_members:  # Không emit cho người mới thêm
                await sio.emit("group_members_updated", {
                    "group_id": group.id,
                    "added_count": len(added_members)
                }, room=f"user_{member.user_id}")

        return {
            "group_id": group_id,
            "added_count": len(added_members),
            "message": f"Đã thêm {len(added_members)} thành viên vào nhóm"
        }
        
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid member_ids format")
    except Exception as e:
        print(f"Error adding members: {e}")
        raise HTTPException(500, "Lỗi thêm thành viên")


@app.get("/groups/{group_id}/members")
def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user)
):
    """Lấy danh sách thành viên của nhóm"""
    me = db.query(User).filter(User.username == username).first()
    
    # Kiểm tra user có trong nhóm không
    my_membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == me.id
    ).first()
    
    if not my_membership:
        raise HTTPException(403, "Bạn không có quyền xem thành viên nhóm này")
    
    # Lấy danh sách thành viên
    members = (
        db.query(GroupMember, User)
        .join(User, GroupMember.user_id == User.id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )
    
    return [
        {
            "user_id": user.id,
            "username": user.username,
            "role": member.role,
            "avatar": user.avatar
        }
        for member, user in members
    ]


@app.get("/groups/{group_id}/available_users")
def get_available_users_for_group(
    group_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user)
):
    """Lấy danh sách bạn bè chưa có trong nhóm để thêm vào"""
    me = db.query(User).filter(User.username == username).first()
    
    # Kiểm tra quyền
    my_membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == me.id
    ).first()
    
    if not my_membership or my_membership.role not in ["owner", "admin"]:
        raise HTTPException(403, "Bạn không có quyền quản lý nhóm này")
    
    # Lấy danh sách bạn bè
    friends = db.query(Friend).filter(
        (Friend.status == "accepted") &
        ((Friend.user_id == me.id) | (Friend.friend_id == me.id))
    ).all()

    friend_users = []
    for f in friends:
        if f.friend_id == me.id:
            u = db.query(User).get(f.user_id)
        else:
            u = db.query(User).get(f.friend_id)
        friend_users.append(u)
    
    # Lấy danh sách thành viên hiện tại của nhóm
    current_members = db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).all()
    current_member_ids = [m.user_id for m in current_members]
    
    # Lọc ra những bạn bè chưa có trong nhóm
    available_users = [
        {
            "id": u.id,
            "username": u.username,
            "avatar": u.avatar
        }
        for u in friend_users
        if u and u.id not in current_member_ids
    ]
    
    return available_users
#  Messages APIs 
@app.get("/messages")
def get_messages(
    receiver_id: int = Query(None),
    group_id: int = Query(None),
    db: Session = Depends(get_db),
    username: str = Depends(get_current_user)
):
    me = db.query(User).filter(User.username == username).first()

    query = db.query(Message).options(joinedload(Message.sender))

    if group_id:
        query = query.filter(Message.group_id == group_id)
    elif receiver_id:
        query = query.filter(
            ((Message.sender_id == me.id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == me.id))
        )
    else:
        # phòng chung - chỉ lấy tin nhắn không có receiver_id và group_id
        query = query.filter(Message.receiver_id == None, Message.group_id == None)

    messages = query.order_by(Message.timestamp.asc()).all()

    return [
        {
            "time": hms_local(m.timestamp),
            "username": m.sender.username if m.sender else "System",
            "message": m.content,
            "sender_id": m.sender_id or 0,
            "receiver_id": m.receiver_id,
            "group_id": m.group_id
        }
        for m in messages
    ]

#  Socket.IO Events 
@sio.event
async def connect(sid, environ):
    print("Client connected:", sid)

@sio.event
async def disconnect(sid):
    print("Client disconnected:", sid)
    session = await sio.get_session(sid)
    username = session.get("username")
    if username:
        # Chỉ gửi thông báo disconnect vào phòng chung với metadata
        await sio.emit("chat_message", {
            "username": "System",
            "sender_id": 0,
            "receiver_id": None,
            "group_id": None
        }, room="public")

@sio.event
async def join_chat(sid, data):
    username = data.get("username")
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    if not user:
        return

    await sio.save_session(sid, {"username": username, "user_id": user.id})
    await sio.enter_room(sid, f"user_{user.id}")   # phòng riêng
    await sio.enter_room(sid, "public")            # phòng chung

    # Chỉ gửi thông báo join vào phòng chung với metadata
    await sio.emit("chat_message", {
    "time": datetime.now(timezone.utc).astimezone(LOCAL_TZ).strftime("%H:%M:%S"),
    "username": "System",
    "message": f"⚡ {username} đã tham gia phòng chat",
    "sender_id": 0,
    "receiver_id": None,
    "group_id": None
    }, room="public")

@sio.event
async def join_group(sid, data):
    group_id = data.get("group_id")
    await sio.enter_room(sid, f"group_{group_id}")

@sio.event
async def send_message(sid, data):
    session = await sio.get_session(sid)
    username = session.get("username")
    sender_id = session.get("user_id")
    content = data.get("message")
    receiver_id = data.get("receiver_id")
    group_id = data.get("group_id")

    # DEBUG: In ra để kiểm tra
    print(f"DEBUG - send_message: sender_id={sender_id}, receiver_id={receiver_id}, group_id={group_id}, content='{content}'")

    db = SessionLocal()
    try:
        # Lưu vào database
        msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            group_id=group_id,
            content=content,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        # Tạo payload với đầy đủ metadata
        payload = {
            "time": hms_local(msg.timestamp),
            "username": username,
            "message": content,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "group_id": group_id
        }

        # Logic gửi tin nhắn
        if group_id:
            # 🔹 Tin nhắn nhóm
            print(f"Sending to group_{group_id}")
            await sio.emit("chat_message", payload, room=f"group_{group_id}")

        elif receiver_id and receiver_id != 0:
            # 🔹 Chat riêng - gửi cho cả 2 người
            print(f"Sending private message between user_{sender_id} and user_{receiver_id}")
            await sio.emit("chat_message", payload, room=f"user_{receiver_id}")
            await sio.emit("chat_message", payload, room=f"user_{sender_id}")

        else:
            # 🔹 Phòng chung
            print("Sending to public room")
            await sio.emit("chat_message", payload, room="public")

    except Exception as e:
        print(f"Error in send_message: {e}")
    finally:
        db.close()

#  Logout với metadata 
@app.get("/logout")
async def logout(request: Request):
    username = request.cookies.get("username")
    resp = RedirectResponse("/login")
    resp.delete_cookie("username")
    
    if username:
        # Gửi thông báo logout vào phòng chung với metadata đầy đủ
        await sio.emit("chat_message", {
            "time": datetime.now(timezone.utc).astimezone(LOCAL_TZ).strftime("%H:%M:%S"),
            "username": "System",
            "message": f"⚠️ {username} đã rời phòng chat",
            "sender_id": 0,
            "receiver_id": None,
            "group_id": None
        }, room="public")
    
    return resp