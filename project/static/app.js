document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById('chat-box');
    const inputMsg = document.getElementById('message');
    const sendBtn = document.getElementById('send');
    const userList = document.getElementById('user-list');
    const roomTitle = document.getElementById('room-title');
    const searchInput = document.getElementById('search-user');
    const searchResults = document.getElementById('search-results');
    const friendRequestsList = document.getElementById('friend-requests');

    const myUserId = parseInt(document.body.dataset.userId);
    const username = document.body.dataset.username;

    let currentReceiverId = null;
    let currentGroupId = null;
    let currentRoom = "global";

    const socket = io();
    socket.emit("join_chat", { username });

    // ===== Functions =====
    function escapeHtml(unsafe) {
        return unsafe.replace(/&/g, "&amp;")
                     .replace(/</g, "&lt;")
                     .replace(/>/g, "&gt;")
                     .replace(/"/g, "&quot;")
                     .replace(/'/g, "&#039;");
    }

    function renderMessage(data) {
        const div = document.createElement("div");
        div.classList.add("msg");
        const safeMsg = escapeHtml(data.message);
        if (data.sender_id === 0) div.classList.add("system"), div.innerHTML = `<div class="bubble">[${data.time}] ${safeMsg}</div>`;
        else if (data.username === username) div.classList.add("self"), div.innerHTML = `<div class="bubble">[${data.time}] <b>${data.username}</b>: ${safeMsg}</div>`;
        else div.classList.add("other"), div.innerHTML = `<div class="bubble">[${data.time}] <b>${data.username}</b>: ${safeMsg}</div>`;
        return div;
    }

    function checkMessageBelongsToCurrentRoom(data) {
        if (data.sender_id === 0) return currentRoom === "global";
        if (currentRoom === "global") return !data.receiver_id && !data.group_id;
        if (currentReceiverId) return !data.group_id && data.receiver_id !== null &&
            ((data.sender_id === currentReceiverId && data.receiver_id === myUserId) ||
             (data.sender_id === myUserId && data.receiver_id === currentReceiverId));
        if (currentGroupId) return data.group_id === currentGroupId;
        return false;
    }

    function sendMessage() {
        const message = inputMsg.value.trim();
        if (message !== "") {
            socket.emit("send_message", { message, receiver_id: currentReceiverId, group_id: currentGroupId });
            inputMsg.value = "";
        }
    }

    function addFriendToSidebar(friend) {
        const li = document.createElement("li");
        li.dataset.room = `user_${friend.user_id}`;
        li.dataset.userId = friend.user_id;
        li.textContent = `👤 ${friend.username}`;
        li.addEventListener("click", () => {
            currentReceiverId = friend.user_id;
            currentGroupId = null;
            currentRoom = `user_${friend.user_id}`;
            roomTitle.textContent = `Chat riêng với ${friend.username}`;
            userList.querySelectorAll("li").forEach(el => el.classList.remove("active"));
            li.classList.add("active");
            fetch(`/messages?receiver_id=${currentReceiverId}`)
                .then(res => res.json())
                .then(data => {
                    chatBox.innerHTML = '';
                    data.forEach(msg => chatBox.appendChild(renderMessage(msg)));
                    chatBox.scrollTop = chatBox.scrollHeight;
                });
        });
        const friendsSection = [...userList.querySelectorAll(".section-title")].find(el => el.textContent.includes("Bạn bè"));
        if (friendsSection) friendsSection.insertAdjacentElement("afterend", li);
        else userList.appendChild(li);
    }

    function addGroupToSidebar(group) {
        const li = document.createElement("li");
        li.dataset.room = `group_${group.group_id}`;
        li.dataset.groupId = group.group_id;
        li.textContent = `👥 ${group.name}`;
        li.addEventListener("click", () => {
            currentReceiverId = null;
            currentGroupId = group.group_id;
            currentRoom = li.dataset.room;
            roomTitle.textContent = group.name;
            userList.querySelectorAll("li").forEach(el => el.classList.remove("active"));
            li.classList.add("active");
            fetch(`/messages?group_id=${currentGroupId}`)
                .then(res => res.json())
                .then(data => {
                    chatBox.innerHTML = '';
                    data.forEach(msg => chatBox.appendChild(renderMessage(msg)));
                    chatBox.scrollTop = chatBox.scrollHeight;
                });
            socket.emit("join_group", { group_id: currentGroupId });
        });

        const groupSection = [...userList.querySelectorAll(".section-title")].find(el => el.textContent.includes("Nhóm"));
        if (groupSection) groupSection.insertAdjacentElement("afterend", li);
        else userList.appendChild(li);
    }

    async function loadFriendRequests() {
        try {
            const res = await fetch('/friends/requests');
            const requests = await res.json();
            friendRequestsList.innerHTML = '';
            requests.forEach(r => {
                const li = document.createElement('li');
                li.innerHTML = `${r.username} <button class="accept-btn" data-id="${r.request_id}" data-user-id="${r.user_id}" data-username="${r.username}">Chấp nhận</button>`;
                friendRequestsList.appendChild(li);
                li.querySelector('.accept-btn').addEventListener('click', async (e) => {
                    const btn = e.target;
                    const friend = { user_id: parseInt(btn.dataset.userId), username: btn.dataset.username };
                    try {
                        await fetch(`/friends/accept/${btn.dataset.id}`, { method: "POST" });
                        btn.textContent = "Đã chấp nhận";
                        btn.disabled = true;
                        addFriendToSidebar(friend);
                    } catch(err){ console.error(err); }
                });
            });
        } catch(err){ console.error(err); }
    }

    async function searchUsers(query) {
        try {
            const res = await fetch(`/users/search?q=${encodeURIComponent(query)}`);
            const users = await res.json();
            searchResults.innerHTML = '';
            users.forEach(u => {
                const li = document.createElement('li');
                li.classList.add('search-item');
                li.innerHTML = `${u.username} <button class="add-friend" data-id="${u.id}">Kết bạn</button>`;
                searchResults.appendChild(li);
                li.querySelector(".add-friend").addEventListener("click", async (e) => {
                    e.preventDefault();
                    const btn = e.target;
                    const resp = await fetch(`/friends/${btn.dataset.id}`, { method: "POST" });
                    const data = await resp.json();
                    if (data.status === "pending") btn.textContent = "Đang chờ";
                    else if (data.status === "exists") btn.textContent = "Đã là bạn";
                    btn.disabled = true;
                });
            });
        } catch(err){ console.error(err); }
    }

    // ==== Tạo nhóm mới ====
   const createGroupBtn = document.getElementById('create-group-btn');
const newGroupNameInput = document.getElementById('new-group-name');
const newGroupMemberSelect = document.getElementById('new-group-member');

if (createGroupBtn && newGroupNameInput && newGroupMemberSelect) {
    createGroupBtn.addEventListener('click', async () => {
        const groupName = newGroupNameInput.value.trim();
        const memberId = parseInt(newGroupMemberSelect.value);
        if (!groupName) { alert("Vui lòng nhập tên nhóm"); return; }
        if (!memberId) { alert("Vui lòng chọn thành viên"); return; }

        try {
            const formData = new FormData();
            formData.append("name", groupName);
            formData.append("member_ids", memberId);;

            // 🔹 Tạo nhóm, không add trực tiếp
            const res = await fetch("/groups/create_with_member", { method: "POST", body: formData });
            const data = await res.json();

            if (data.group_id) {
                // socket sẽ emit "new_group" => JS lắng nghe và add vào sidebar
                newGroupNameInput.value = "";
                newGroupMemberSelect.value = "";
                alert(`Nhóm "${data.name}" đã được tạo`);
            } else {
                alert("Tạo nhóm thất bại");
            }
        } catch(err) {
            console.error(err);
            alert("Lỗi tạo nhóm");
        }
    });
}

    // ==== Event listeners chat ====
    sendBtn.onclick = sendMessage;
    inputMsg.addEventListener("keypress", e => { if(e.key === "Enter") sendMessage(); });

    userList.querySelectorAll("li[data-room]").forEach(li => {
        li.addEventListener("click", () => {
            userList.querySelectorAll("li").forEach(el => el.classList.remove("active"));
            li.classList.add("active");
            currentReceiverId = li.dataset.userId ? parseInt(li.dataset.userId) : null;
            currentGroupId = li.dataset.groupId ? parseInt(li.dataset.groupId) : null;
            currentRoom = li.dataset.room;
            if(currentReceiverId) roomTitle.textContent = `Chat riêng với ${li.textContent.replace('👤 ', '')}`;
            else if(currentGroupId){ 
                roomTitle.textContent = li.textContent.replace('👥 ', '');
                socket.emit("join_group", { group_id: currentGroupId }); 
            } else roomTitle.textContent = "Phòng chung";

            let url = "/messages";
            if(currentReceiverId) url += "?receiver_id=" + currentReceiverId;
            else if(currentGroupId) url += "?group_id=" + currentGroupId;

            fetch(url)
                .then(res => res.json())
                .then(data => {
                    chatBox.innerHTML = '';
                    data.forEach(msg => chatBox.appendChild(renderMessage(msg)));
                    chatBox.scrollTop = chatBox.scrollHeight;
                });
        });
    });

    searchInput.addEventListener('input', async () => {
        const query = searchInput.value.trim();
        if(!query) searchResults.innerHTML = '';
        else searchUsers(query);
    });

    socket.on("chat_message", function(data){
        if(checkMessageBelongsToCurrentRoom(data)){
            chatBox.appendChild(renderMessage(data));
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    });

    socket.on("new_group", function(group) {
        addGroupToSidebar(group);
    });

    // ==== Initial load ====
    loadFriendRequests();
    setInterval(loadFriendRequests, 10000);
});
