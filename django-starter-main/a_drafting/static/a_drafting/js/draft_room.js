document.addEventListener("DOMContentLoaded", () => {
    const draftRoom = document.getElementById("draft-room");
    const draftId = draftRoom.getAttribute("data-draft-id");
    const socket = new WebSocket(`ws://${window.location.host}/ws/drafts/${draftId}/`);

    socket.onopen = function () {
        console.log("WebSocket connection established.");
    };

    socket.onmessage = function (event) {
        console.log("WebSocket message received:", event.data);
        const data = JSON.parse(event.data);

        if (data.type === "draft.pack") {
            console.log("Draft pack data received:", data.cards);
            displayDraftPack(data.cards);
        } else if (data.type === "waiting") {
            displayWaitingMessage(data.message);
        } else if (data.type === "draft.complete") {
            console.log("Draft complete data received:", data.cards);
            if (data.cards && data.cards.length > 0) {
                displayDraftedCards(data.cards);
            } else {
                console.error("Draft complete received but no cards data available.");
            }
        } else if (data.type === "player.update") {
            console.log("Player list:", data.players);
            updatePlayerList(data.players);
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

    if (startDraftButton) {
        startDraftButton.addEventListener("click", async () => {
            try {
                console.log("Sending draft start request...");
                const response = await fetch(`/drafting/drafts/${draftId}/start-draft/`, {
                    method: "POST",
                    headers: { "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value },
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log("Draft start response:", data);
                    alert(data.message);
                    console.log("Sending WebSocket message:", JSON.stringify({ type: "start.draft", draft_id: draftId }));
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
    }

    const displayDraftPack = (cards) => {
        const packDisplaySection = document.getElementById("pack-display-section");
        const packDisplay = document.getElementById("pack-display");
      
        packDisplaySection.style.display = "block"; // Ensure visibility
        packDisplay.innerHTML = ""; // Clear previous content
    
        cards.forEach((card) => {
            const cardContainer = document.createElement("div");
            cardContainer.className = "card-container";
    
            const cardImg = document.createElement("img");
            cardImg.src = card.image_url || '/static/images/default_card.png';
            cardImg.alt = card.name;
            cardImg.className = "card-img";
    
            const cardName = document.createElement("p");
            cardName.textContent = card.name;
            cardName.className = "card-name";
    
            const draftButton = document.createElement("button");
            draftButton.textContent = "Draft This Card";
            draftButton.className = "draft-button";
            draftButton.onclick = () => draftCard(card.name);
    
            cardContainer.appendChild(cardImg);
            cardContainer.appendChild(cardName);
            cardContainer.appendChild(draftButton);
            packDisplay.appendChild(cardContainer);
        });
    };
    
      
    const draftCard = (cardName) => {
        console.log(`Drafting card: ${cardName}`);
        socket.send(JSON.stringify({ type: "draft.card", card: cardName }));
    
        // Temporarily display a waiting message until the next pack is received
        displayWaitingMessage("Waiting for other players to draft...");
    };
    

    const displayWaitingMessage = (message) => {
        const packDisplaySection = document.getElementById("pack-display-section");
        const packDisplay = document.getElementById("pack-display");
    
        packDisplaySection.style.display = "block";
        packDisplay.innerHTML = `<p>${message}</p>`;
    };

    const updatePlayerList = (players) => {
        const playerList = document.getElementById("player-list");
        playerList.innerHTML = "";
        players.forEach(player => {
            const li = document.createElement("li");
            li.textContent = player.username;
            playerList.appendChild(li);
        });

    }; 

    function displayDraftedCards(cards) {
        const draftResultsContainer = document.getElementById("draft-results");
        draftResultsContainer.innerHTML = ""; // Clear any existing content
    
        const header = document.createElement("h3");
        header.textContent = "Your Drafted Cards";
        draftResultsContainer.appendChild(header);
    
        const cardList = document.createElement("ul");
        cards.forEach(card => {
            const cardItem = document.createElement("li");
            cardItem.innerHTML = `
                <img src="${card.image_url || '/static/images/default_card.png'}" alt="${card.name}" />
                <span>${card.name}</span>
            `;
            cardList.appendChild(cardItem);
        });
    
        draftResultsContainer.appendChild(cardList);
    }
    ;
});
