const chatInput = document.getElementById("chatInput");

chatInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight)+ "px";
});
