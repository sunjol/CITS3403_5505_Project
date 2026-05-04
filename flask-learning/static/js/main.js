async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
    }
    return response.json();
}

const cycleButton = document.querySelector("#load-cycle");
const cycleList = document.querySelector("#cycle-list");

if (cycleButton && cycleList) {
    cycleButton.addEventListener("click", async () => {
        cycleList.innerHTML = "<li>Loading from /api/server-cycle...</li>";
        try {
            const data = await fetchJson("/api/server-cycle");
            cycleList.innerHTML = data.steps
                .map((step) => `<li>${step}</li>`)
                .join("");
        } catch (error) {
            cycleList.innerHTML = `<li>${error.message}</li>`;
        }
    });
}

const topicFeed = document.querySelector("#topic-feed");

if (topicFeed) {
    topicFeed.innerHTML = "<p class='info-box'>Loading topics from /api/topics...</p>";

    fetchJson("/api/topics")
        .then((topics) => {
            topicFeed.innerHTML = topics
                .map((topic) => `
                    <article class="card">
                        <p class="tag">${topic.category}</p>
                        <h2>${topic.title}</h2>
                        <p>${topic.summary}</p>
                        <p class="checkpoint"><strong>Checkpoint:</strong> ${topic.checkpoint}</p>
                    </article>
                `)
                .join("");
        })
        .catch((error) => {
            topicFeed.innerHTML = `<p class="info-box">${error.message}</p>`;
        });
}
