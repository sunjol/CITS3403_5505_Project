// Form submission handler
document.getElementById("myForm").addEventListener("submit", function (event) {
  event.preventDefault(); // Prevent page reload

  const name = document.getElementById("nameInput").value;
  document.getElementById("output").textContent = `Hello, ${name}`;
});

// Button click handler
document.getElementById("fetchButton").addEventListener("click", fetchData);

// API fetching function
async function fetchData() {
  const output = document.getElementById("output");

  try {
    const response = await fetch(
      "https://jsonplaceholder.typicode.com/todos/3",
    );

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    const data = await response.json();
    output.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    output.textContent = `Error: ${error.message}`;
  }
}
