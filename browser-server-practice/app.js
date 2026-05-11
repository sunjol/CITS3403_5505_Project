const API_URL = "https://jsonplaceholder.typicode.com/posts";

// Buttons
document.getElementById("loadBtn").addEventListener("click", loadPosts);
document.getElementById("clearBtn").addEventListener("click", clearPosts);
document.getElementById("postBtn").addEventListener("click", createPost);
document.getElementById("asyncBtn").addEventListener("click", showAsyncTiming);

// GET request
async function loadPosts() {
    const status = document.getElementById("getStatus");
    const container = document.getElementById("posts");

    status.textContent = "Loading...";
    container.innerHTML = "";

    try {
        const response = await fetch(API_URL + "?_limit=5");

        if (!response.ok) {
            throw new Error("HTTP error: " + response.status);
        }

        const posts = await response.json();

        status.textContent = "Loaded successfully";

        posts.forEach((post) => {
            const div = document.createElement("div");
            div.innerHTML = `<h3>${post.title}</h3><p>${post.body}</p>`;
            container.appendChild(div);
        });
    } catch (err) {
        status.textContent = "Error: " + err.message;
    }
}

// POST request
async function createPost() {
    const title = document.getElementById("title").value;
    const body = document.getElementById("body").value;

    const status = document.getElementById("postStatus");
    const output = document.getElementById("postResponse");

    if (!title || !body) {
        status.textContent = "Fill all fields";
        return;
    }

    status.textContent = "Sending...";

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                title: title,
                body: body,
                userId: 1,
            }),
        });

        if (!response.ok) {
            throw new Error("HTTP error: " + response.status);
        }

        const data = await response.json();

        status.textContent = "Success";
        output.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        status.textContent = "Error: " + err.message;
    }
}

// Clear content
function clearPosts() {
    document.getElementById("posts").innerHTML = "";
    document.getElementById("getStatus").textContent = "Cleared";
}

// Async demo
async function showAsyncTiming() {
    const output = document.getElementById("timingOutput");

    output.textContent = "1. Start\n";

    const randomId = Math.floor(Math.random() * 100) + 1;
    const promise = fetch(API_URL + "/" + randomId);

    output.textContent += "2. Request sent\n";
    output.textContent += "3. JS continues running\n";

    const response = await promise;
    const data = await response.json();

    output.textContent += "4. Response received\n";
    output.textContent += "5. Title: " + data.title;
}
