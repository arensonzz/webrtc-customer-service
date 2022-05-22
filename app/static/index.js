// Put these JavaScript codes to the HTML file of the route
// you want socket connections to happen.
const socket = io("/live-chat");

const form = document.getElementById("form");
const input = document.getElementById("input");
const messageContainer = document.getElementById("messageContainer");
const leaveButton = document.getElementById("leaveButton");

// Emit joined event to inform other users in the room
socket.on("connect", () => {
  socket.emit("joined", {});
  console.log("SocketIO: Connected to server");
});

function appendMessage(msgHtml) {
  messageContainer.insertAdjacentHTML("beforeend", msgHtml);
  // Scroll message container to bottom when new message arrives
  messageContainer.scrollTop = messageContainer.scrollHeight;
}

// Add the status message to DOM
socket.on("status", (data) => {
  let newItem = `
    <div class="row gap-1 mb-2">
      <div class="message-text col me-2 text-muted">${data.msg}</div>
    </div>
  `;
  appendMessage(newItem);
});

// Add the chat message to DOM
socket.on("message", (data) => {
  let newItem = `
    <div class="mb-2 d-flex flex-row flex-nowrap">
      <div class="message-info me-3 p-1 align-self-end  bg-secondary text-white rounded-2">
        ${data.user}
      </div>
      <div class="dialog-box">
        <div class="arrow">
          <div class="outer"></div>
          <div class="inner"></div>
        </div>
      </div>
      <div class="message-text p-1 border border-1 rounded-2 flex-grow-1">
        <div>${data.msg}</div>
      </div>
    </div>
  `;
  appendMessage(newItem);
});

// Send message with enter (hidden submit button)
form.addEventListener("submit", function (e) {
  e.preventDefault();
  if (input.value) {
    socket.emit("message", {msg: input.value});
    input.value = "";
  }
});

// Leave room by clicking the button
function leaveRoom() {
  socket.emit("left", {}, () => {
    socket.disconnect();
    window.location.href = "/leave-chat";
  });
}

leaveButton.addEventListener("click", () => {
  isLeave = confirm("Do you want to leave the chat?");

  if (isLeave) {
    leaveRoom();
  }
});

// Leave room before leaving page
/* window.onbeforeunload = () => {
  leaveRoom();
  return "Do you want to leave chat?";
}; */
