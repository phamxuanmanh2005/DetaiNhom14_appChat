document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById('chat-box');
    const inputMsg = document.getElementById('message');
    const sendBtn = document.getElementById('send');
    const userList = document.getElementById('user-list');
    const roomTitle = document.getElementById('room-title');
    const searchInput = document.getElementById('search-user');
    const searchResults = document.getElementById('search-results');
    const friendRequestsList = document.getElementById('friend-requests');
    
    // Group management elements
    const groupManagement = document.getElementById('group-management');
    const closeManagementBtn = document.querySelector('.close-management');
    const addMembersBtn = document.getElementById('add-members-btn');
    const addGroupMembers = document.getElementById('add-group-members');
    const addSelectedCount = document.getElementById('add-selected-count');
    const manageGroupTitle = document.getElementById('manage-group-title');

    const myUserId = parseInt(document.body.dataset.userId);
    const username = document.body.dataset.username;

    let currentReceiverId = null;
    let currentGroupId = null;
    let currentRoom = "global";
    let currentManagingGroupId = null;

    // ✅ FIX: Đảm bảo phòng chung được active khi load trang
    function initializeDefaultRoom() {
        const globalRoomElement = userList.querySelector('li[data-room="global"]');
        if (globalRoomElement) {
            currentRoom = "global";
            currentReceiverId = null;
            currentGroupId = null;
            globalRoomElement.classList.add("active");
            roomTitle.textContent = "Phòng chung";
        }
    }

    // Arrays để track selected members
    let selectedNewGroupMembers = [];
    let selectedAddMembers = [];

    const socket = io();
    socket.emit("join_chat", { username });

    // Functions 
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

    // ✅ FIX: Logic lọc tin nhắn với kiểm tra chặt chẽ hơn
    function checkMessageBelongsToCurrentRoom(data) {
        // Tin nhắn hệ thống (system messages) - chỉ hiện ở phòng chung
        if (data.sender_id === 0) {
            return currentRoom === "global" && data.receiver_id === null && data.group_id === null;
        }
        
        // ✅ Kiểm tra chính xác theo từng loại phòng
        if (currentRoom === "global") {
            // Phòng chung: chỉ tin nhắn không có receiver_id và group_id
            return data.receiver_id === null && data.group_id === null;
        }
        
        if (currentReceiverId !== null) {
            // Chat riêng: chỉ tin nhắn giữa 2 user cụ thể, không thuộc group
            return data.group_id === null && 
                   data.receiver_id !== null && 
                   ((data.sender_id === currentReceiverId && data.receiver_id === myUserId) ||
                    (data.sender_id === myUserId && data.receiver_id === currentReceiverId));
        }
        
        if (currentGroupId !== null) {
            // Chat nhóm: chỉ tin nhắn của group hiện tại
            return data.group_id === currentGroupId && data.receiver_id === null;
        }
        
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
        li.addEventListener("click", () => switchToRoom(li, friend.user_id, null, `Chat riêng với ${friend.username}`));
        
        const friendsSection = [...userList.querySelectorAll(".section-title")].find(el => el.textContent.includes("Bạn bè"));
        if (friendsSection) friendsSection.insertAdjacentElement("afterend", li);
        else userList.appendChild(li);
    }

    function addGroupToSidebar(group) {
        const li = document.createElement("li");
        li.classList.add("group-item");
        li.dataset.room = `group_${group.group_id}`;
        li.dataset.groupId = group.group_id;
        
        const groupName = document.createElement("span");
        groupName.classList.add("group-name");
        groupName.textContent = `👥 ${group.name}`;
        
        const manageBtn = document.createElement("button");
        manageBtn.classList.add("group-manage-btn");
        manageBtn.dataset.groupId = group.group_id;
        manageBtn.dataset.groupName = group.name;
        manageBtn.textContent = "⚙️";
        manageBtn.title = "Quản lý nhóm";
        
        li.appendChild(groupName);
        li.appendChild(manageBtn);
        
        // Click vào tên nhóm để vào chat
        groupName.addEventListener("click", () => {
            switchToRoom(li, null, group.group_id, group.name);
            socket.emit("join_group", { group_id: group.group_id });
        });
        
        // Click vào nút quản lý
        manageBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            openGroupManagement(group.group_id, group.name);
        });

        const groupSection = [...userList.querySelectorAll(".section-title")].find(el => el.textContent.includes("Nhóm"));
        if (groupSection) {
            const groupsList = document.getElementById('groups-list');
            if (groupsList) {
                groupsList.appendChild(li);
            } else {
                groupSection.insertAdjacentElement("afterend", li);
            }
        } else {
            userList.appendChild(li);
        }
    
        // Gắn lại event cho tất cả group buttons sau khi thêm mới
        setTimeout(() => {
            document.querySelectorAll('.group-manage-btn').forEach(btn => {
                btn.onclick = null; // Xóa event cũ để tránh duplicate
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const groupId = parseInt(btn.dataset.groupId);
                    const groupName = btn.dataset.groupName;
                    openGroupManagement(groupId, groupName);
                });
            });
        }, 100);
    }

    // ✅ FIX: Cập nhật logic switchToRoom để đảm bảo currentRoom được set đúng
    function switchToRoom(element, receiverId, groupId, title) {
        currentReceiverId = receiverId;
        currentGroupId = groupId;
        
        // ✅ Set currentRoom chính xác dựa vào loại phòng
        if (receiverId) {
            currentRoom = `user_${receiverId}`;
        } else if (groupId) {
            currentRoom = `group_${groupId}`;
        } else {
            currentRoom = "global";
        }
        
        console.log('Switched to room:', {
            currentRoom: currentRoom,
            receiverId: receiverId,
            groupId: groupId
        });
        
        roomTitle.textContent = title;
        
        userList.querySelectorAll("li").forEach(el => el.classList.remove("active"));
        element.classList.add("active");
        
        let url = "/messages";
        if (receiverId) url += "?receiver_id=" + receiverId;
        else if (groupId) url += "?group_id=" + groupId;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                chatBox.innerHTML = '';
                data.forEach(msg => chatBox.appendChild(renderMessage(msg)));
                chatBox.scrollTop = chatBox.scrollHeight;
            });
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

    //  Member button functions 
    function updateSelectedCount(selectedArray, countElement) {
        countElement.textContent = selectedArray.length;
        return selectedArray.length;
    }

    function toggleMemberSelection(userId, username, selectedArray, button) {
        const index = selectedArray.findIndex(member => member.id === userId);
        
        if (index === -1) {
            // Add member - lần click đầu
            selectedArray.push({ id: userId, username: username });
            button.classList.add('selected');
            button.textContent = 'Đã thêm';
        } else {
            // Remove member - lần click thứ 2 để hủy
            selectedArray.splice(index, 1);
            button.classList.remove('selected');
            button.textContent = 'Thêm';
        }
    }

    function setupMemberButtons(container, selectedArray, countElement, submitButton) {
        const buttons = container.querySelectorAll('.add-member-btn');
        buttons.forEach(button => {
            button.onclick = null; // Clear existing events
            button.addEventListener('click', () => {
                const userId = parseInt(button.dataset.userId);
                const username = button.dataset.username;
                
                toggleMemberSelection(userId, username, selectedArray, button);
                const count = updateSelectedCount(selectedArray, countElement);
                submitButton.disabled = count === 0;
            });
        });
    }

    //  Group Management 
    async function openGroupManagement(groupId, groupName) {
        currentManagingGroupId = groupId;
        manageGroupTitle.textContent = `⚙️ Quản lý nhóm: ${groupName}`;
        
        try {
            // Load available users for this group
            const res = await fetch(`/groups/${groupId}/available_users`);
            const availableUsers = await res.json();
            
            // Clear and populate the add members list
            addGroupMembers.innerHTML = '';
            selectedAddMembers = []; // Reset selection
            
            availableUsers.forEach(user => {
                const memberItem = document.createElement('div');
                memberItem.classList.add('member-item');
                
                const memberName = document.createElement('span');
                memberName.classList.add('member-name');
                memberName.textContent = user.username;
                
                const button = document.createElement('button');
                button.classList.add('add-member-btn');
                button.dataset.userId = user.id;
                button.dataset.username = user.username;
                button.textContent = 'Thêm';
                
                memberItem.appendChild(memberName);
                memberItem.appendChild(button);
                addGroupMembers.appendChild(memberItem);
            });
            
            // Setup button events
            setupMemberButtons(addGroupMembers, selectedAddMembers, addSelectedCount, addMembersBtn);
            
            updateSelectedCount(selectedAddMembers, addSelectedCount);
            addMembersBtn.disabled = true;
            groupManagement.classList.add('active');
            
        } catch (err) {
            console.error('Error loading available users:', err);
            alert('Không thể tải danh sách người dùng');
        }
    }

    function closeGroupManagement() {
        groupManagement.classList.remove('active');
        currentManagingGroupId = null;
        addGroupMembers.innerHTML = '';
        selectedAddMembers = [];
        updateSelectedCount(selectedAddMembers, addSelectedCount);
    }

    //  Tạo nhóm mới với member buttons 
    const createGroupBtn = document.getElementById('create-group-btn');
    const newGroupNameInput = document.getElementById('new-group-name');
    const newGroupMembers = document.getElementById('new-group-members');
    const selectedCount = document.getElementById('selected-count');

    // Setup member buttons for create group
    if (newGroupMembers && selectedCount && createGroupBtn) {
        setupMemberButtons(newGroupMembers, selectedNewGroupMembers, selectedCount, createGroupBtn);
        
        // Initialize count
        updateSelectedCount(selectedNewGroupMembers, selectedCount);
        createGroupBtn.disabled = true;
    }

    if (createGroupBtn && newGroupNameInput && newGroupMembers) {
        createGroupBtn.addEventListener('click', async () => {
            const groupName = newGroupNameInput.value.trim();
            const selectedMemberIds = selectedNewGroupMembers.map(member => member.id);
            
            if (!groupName) { 
                alert("Vui lòng nhập tên nhóm"); 
                return; 
            }
            if (selectedMemberIds.length === 0) { 
                alert("Vui lòng chọn ít nhất 1 thành viên"); 
                return; 
            }

            try {
                const formData = new FormData();
                formData.append("name", groupName);
                formData.append("member_ids", JSON.stringify(selectedMemberIds));

                const res = await fetch("/groups/create_with_members", { 
                    method: "POST", 
                    body: formData 
                });
                const data = await res.json();

                if (data.group_id) {
                    // Reset form
                    newGroupNameInput.value = "";
                    selectedNewGroupMembers = [];
                    
                    // Reset all buttons
                    newGroupMembers.querySelectorAll('.add-member-btn').forEach(btn => {
                        btn.classList.remove('selected');
                        btn.textContent = 'Thêm';
                    });
                    
                    updateSelectedCount(selectedNewGroupMembers, selectedCount);
                    createGroupBtn.disabled = true;
                    
                    alert(`Nhóm "${data.name}" đã được tạo với ${data.member_count} thành viên`);
                } else {
                    alert("Tạo nhóm thất bại");
                }
            } catch(err) {
                console.error(err);
                alert("Lỗi tạo nhóm");
            }
        });
    }

    // Add members to existing group
    if (addMembersBtn) {
        addMembersBtn.addEventListener('click', async () => {
            const selectedMemberIds = selectedAddMembers.map(member => member.id);
            
            if (selectedMemberIds.length === 0) {
                alert("Vui lòng chọn ít nhất 1 thành viên");
                return;
            }

            try {
                const formData = new FormData();
                formData.append("member_ids", JSON.stringify(selectedMemberIds));

                const res = await fetch(`/groups/${currentManagingGroupId}/add_members`, {
                    method: "POST",
                    body: formData
                });
                const data = await res.json();

                if (data.added_count > 0) {
                    alert(`Đã thêm ${data.added_count} thành viên vào nhóm`);
                    closeGroupManagement();
                } else {
                    alert("Không thể thêm thành viên");
                }
            } catch(err) {
                console.error(err);
                alert("Lỗi thêm thành viên");
            }
        });
    }

    // Close group management
    if (closeManagementBtn) {
        closeManagementBtn.addEventListener('click', closeGroupManagement);
    }

    //  Event listeners 
    sendBtn.onclick = sendMessage;
    inputMsg.addEventListener("keypress", e => { if(e.key === "Enter") sendMessage(); });

    // Existing room click handlers
    userList.querySelectorAll("li[data-room]").forEach(li => {
        // Chỉ gắn event cho những item không phải group-item
        if (!li.classList.contains('group-item')) {
            li.addEventListener("click", () => {
                const receiverId = li.dataset.userId ? parseInt(li.dataset.userId) : null;
                const groupId = li.dataset.groupId ? parseInt(li.dataset.groupId) : null;
                
                let title = "Phòng chung";
                if (receiverId) {
                    title = `Chat riêng với ${li.textContent.replace('👤 ', '')}`;
                } else if (groupId) {
                    title = li.textContent.replace('👥 ', '');
                    socket.emit("join_group", { group_id: groupId });
                }
                
                switchToRoom(li, receiverId, groupId, title);
            });
        }
    });

    // Gắn event listener cho các nút group management có sẵn
    document.querySelectorAll('.group-manage-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const groupId = parseInt(btn.dataset.groupId);
            const groupName = btn.dataset.groupName;
            openGroupManagement(groupId, groupName);
        });
    });

    // Gắn event cho group names để vào chat
    document.querySelectorAll('.group-name').forEach(groupName => {
        groupName.addEventListener('click', () => {
            const groupItem = groupName.closest('.group-item');
            const groupId = parseInt(groupItem.dataset.groupId);
            const title = groupName.textContent.replace('👥 ', '');
            
            switchToRoom(groupItem, null, groupId, title);
            socket.emit("join_group", { group_id: groupId });
        });
    });

    // Search functionality
    searchInput.addEventListener('input', async () => {
        const query = searchInput.value.trim();
        if(!query) searchResults.innerHTML = '';
        else searchUsers(query);
    });

    // ✅ Socket events với logging để debug
    socket.on("chat_message", function(data){
        console.log('Received message:', data);
        const shouldShow = checkMessageBelongsToCurrentRoom(data);
        console.log('Should show message:', shouldShow);
        
        if(shouldShow){
            chatBox.appendChild(renderMessage(data));
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    });

    socket.on("new_group", function(group) {
        addGroupToSidebar(group);
    });

    socket.on("group_members_updated", function(data) {
        // Show notification about new members added
        if (data.group_id !== currentGroupId) {
            // Could show a notification here
            console.log(`${data.added_count} new members added to group ${data.group_id}`);
        }
    });

    // ✅ FIX: Load lại tin nhắn phòng chung khi khởi tạo
    function loadGlobalRoomMessages() {
        fetch('/messages')  // Load tin nhắn phòng chung (không có receiver_id, group_id)
            .then(res => res.json())
            .then(data => {
                chatBox.innerHTML = '';
                // Chỉ hiển thị tin nhắn phòng chung (không có receiver_id và group_id)
                data.filter(msg => !msg.receiver_id && !msg.group_id)
                    .forEach(msg => chatBox.appendChild(renderMessage(msg)));
                chatBox.scrollTop = chatBox.scrollHeight;
            })
            .catch(err => console.error('Error loading messages:', err));
    }

    //  Initial load 
    // ✅ FIX: Khởi tạo và load lại tin nhắn phòng chung
    initializeDefaultRoom();
    loadGlobalRoomMessages();
    loadFriendRequests();
    setInterval(loadFriendRequests, 10000);
});