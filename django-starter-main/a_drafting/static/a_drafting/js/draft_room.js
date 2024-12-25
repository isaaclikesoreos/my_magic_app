document.addEventListener("DOMContentLoaded", () => {
    // Get the draft ID from the HTML data attribute
    const draftRoom = document.getElementById("draft-room");
    const draftId = draftRoom.getAttribute("data-draft-id");

    // Initialize WebSocket
    const socket = new WebSocket(`ws://${window.location.host}/ws/drafts/${draftId}/`);

    socket.onopen = function () {
        console.log("WebSocket connection established.");
    };

    socket.onmessage = function (event) {
        console.log("WebSocket message received:", event.data);
        const data = JSON.parse(event.data);
    
        if (data.type === "player.update") {
            console.log("player list:", data.players);
            // Update the player list
            const playerList = document.getElementById("player-list");
            playerList.innerHTML = "";
            data.players.forEach(player => {
                const li = document.createElement("li");
                li.textContent = player.username;
                playerList.appendChild(li);
            });
        } else if (data.type === "draft.pack") {
            console.log("Draft pack data:", data.cards);
            // Display the draft pack
            const packDisplaySection = document.getElementById("pack-display-section");
            const packDisplay = document.getElementById("pack-display");
    
            packDisplaySection.style.display = "block";
            packDisplay.innerHTML = "";
    
            data.cards.forEach(card => {
                const cardImg = document.createElement("img");
                cardImg.src = card.image_url;
                cardImg.alt = card.name;
                packDisplay.appendChild(cardImg);
            });
        } else if (data.type === "start.draft") {
            alert(data.message);
        }
    };
    

    socket.onclose = function () {
        console.log("WebSocket connection closed.");
    };

    socket.onerror = function (error) {
        console.error("WebSocket error:", error);
    };

    const startDraftButton = document.getElementById("start-draft-btn");
    const packDisplay = document.getElementById("pack-display");

    startDraftButton.addEventListener("click", async () => {
        try {
            onsole.log("Sending draft start request...");
            const response = await fetch(`/drafting/drafts/${draftId}/start-draft/`, {
                method: "POST",
                headers: { "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value },
            });

            if (response.ok) {
                const data = await response.json();
                console.log("Draft start response:", data);
                alert(data.message);
                socket.send(JSON.stringify({ type: "start.draft", draft_id: draftId }));
            } else {
                const error = await response.json();
                console.error("Draft start error:", error);
                alert(error.error);
            }
        } catch (err) {
            console.error("Error starting draft:", err);
        }
    });

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        if (data.type === "draft.pack") {
            packDisplay.innerHTML = "";
            data.cards.forEach((card) => {
                const cardImg = document.createElement("img");
                cardImg.src = card.image_url;
                cardImg.alt = card.name;
                packDisplay.appendChild(cardImg);
            });
        }
    };
});
