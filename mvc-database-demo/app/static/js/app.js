let groups = window.INITIAL_GROUPS || [];

const groupsEl = document.querySelector("#groups");
const messageEl = document.querySelector("#message");
const studentGroupSelect = document.querySelector("#student-group");

function showMessage(text, isError = false) {
  messageEl.textContent = text;
  messageEl.style.color = isError ? "#b42318" : "#027a48";
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }
  return data;
}

async function refreshGroups() {
  groups = await requestJson("/api/groups");
  render();
}

function renderGroupOptions() {
  studentGroupSelect.innerHTML = groups
    .map(group => `<option value="${group.id}">${group.name}</option>`)
    .join("");
}

function renderGroups() {
  if (groups.length === 0) {
    groupsEl.innerHTML = `<p class="muted">No groups yet. Create one first.</p>`;
    return;
  }

  groupsEl.innerHTML = groups.map(group => `
    <article class="group">
      <h3>${group.name} <span class="muted">#${group.id}</span></h3>
      ${group.students.length === 0 ? `<p class="muted" style="padding: 1rem;">No students in this group.</p>` : ""}
      ${group.students.map(student => `
        <form class="student" data-student-id="${student.id}">
          <label>
            Name
            <input name="name" value="${student.name}" />
          </label>
          <label>
            Email
            <input name="email" type="email" value="${student.email}" />
          </label>
          <div>
            <button type="submit">Update</button>
            <button class="danger" type="button" data-delete-id="${student.id}">Delete</button>
          </div>
        </form>
      `).join("")}
    </article>
  `).join("");
}

function render() {
  renderGroupOptions();
  renderGroups();
}

document.querySelector("#group-form").addEventListener("submit", async event => {
  event.preventDefault();
  const name = document.querySelector("#group-name").value;

  try {
    await requestJson("/api/groups", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    event.target.reset();
    await refreshGroups();
    showMessage("Group created. That is a CREATE operation.");
  } catch (error) {
    showMessage(error.message, true);
  }
});

document.querySelector("#student-form").addEventListener("submit", async event => {
  event.preventDefault();

  const payload = {
    name: document.querySelector("#student-name").value,
    email: document.querySelector("#student-email").value,
    group_id: Number(document.querySelector("#student-group").value),
  };

  try {
    await requestJson("/api/students", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    event.target.reset();
    await refreshGroups();
    showMessage("Student created. The ORM inserted a new row into SQLite.");
  } catch (error) {
    showMessage(error.message, true);
  }
});

groupsEl.addEventListener("submit", async event => {
  if (!event.target.matches(".student")) return;
  event.preventDefault();

  const studentId = event.target.dataset.studentId;
  const formData = new FormData(event.target);

  try {
    await requestJson(`/api/students/${studentId}`, {
      method: "PATCH",
      body: JSON.stringify({
        name: formData.get("name"),
        email: formData.get("email"),
      }),
    });
    await refreshGroups();
    showMessage("Student updated. That is an UPDATE operation.");
  } catch (error) {
    showMessage(error.message, true);
  }
});

groupsEl.addEventListener("click", async event => {
  const deleteId = event.target.dataset.deleteId;
  if (!deleteId) return;

  try {
    await requestJson(`/api/students/${deleteId}`, { method: "DELETE" });
    await refreshGroups();
    showMessage("Student deleted. That is a DELETE operation.");
  } catch (error) {
    showMessage(error.message, true);
  }
});

document.querySelector("#reset-button").addEventListener("click", async () => {
  try {
    groups = await requestJson("/api/reset", { method: "POST" });
    render();
    showMessage("Demo data reset.");
  } catch (error) {
    showMessage(error.message, true);
  }
});

render();
