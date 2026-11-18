const byId = (id) => document.getElementById(id);
const auth = byId("auth");
const ingredient = byId("ingredient");
const generate = byId("generate");
let token = sessionStorage.getItem("alacena-token");
let editing = null;
let authMode = "login";
let toastTimer;

const AUTH_TEXT = {
  login: { title: "Bienvenido de nuevo", hint: "Ingresa a tu alacena para continuar.", submit: "Iniciar sesión", autocomplete: "current-password" },
  register: { title: "Crea tu cuenta", hint: "Solo necesitas un correo y una contraseña de 8 caracteres o más.", submit: "Crear cuenta", autocomplete: "new-password" },
};

function notify(message = "", error = false) {
  const toast = byId("toast");
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.hidden = !message;
  toast.classList.toggle("error", error);
  if (message) toastTimer = setTimeout(() => { toast.hidden = true; }, error ? 6000 : 3500);
}

function view() {
  byId("access").hidden = Boolean(token);
  byId("workspace").hidden = !token;
  byId("logout").hidden = !token;
}

function logout() {
  token = null;
  sessionStorage.removeItem("alacena-token");
  resetIngredient();
  byId("ingredients").replaceChildren();
  byId("recipes").replaceChildren();
  view();
}

async function api(path, method = "GET", payload) {
  const activeToken = token;
  const response = await fetch("/api" + path, {
    method,
    headers: {
      ...(activeToken && { Authorization: "Bearer " + activeToken }),
      ...(payload && { "Content-Type": "application/json" }),
    },
    body: payload && JSON.stringify(payload),
  });
  if (response.status === 204) return;
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && activeToken && token === activeToken) {
      logout();
      throw new Error("La sesión venció. Inicia sesión de nuevo.");
    }
    throw new Error(typeof result.detail === "string" ? result.detail : "Revisa los datos ingresados.");
  }
  return result;
}

async function run(control, task) {
  control.disabled = true;
  try { await task(); }
  catch (error) { notify(error.message, true); }
  finally { control.disabled = false; }
}

function element(tag, text = "", className = "") {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function action(label, task, className = "ghost icon", title = "") {
  const button = element("button", label, className);
  button.type = "button";
  if (title) { button.title = title; button.setAttribute("aria-label", title); }
  button.addEventListener("click", () => run(button, task));
  return button;
}

function emptyState(icon, text, tag = "div") {
  const box = element(tag, "", "empty");
  box.append(element("span", icon), document.createTextNode(text));
  return box;
}

/* ---------- Autenticación ---------- */
function setAuthMode(mode) {
  authMode = mode;
  const text = AUTH_TEXT[mode];
  for (const tab of auth.querySelectorAll(".tab")) {
    const active = tab.dataset.mode === mode;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
  }
  byId("auth-title").textContent = text.title;
  byId("auth-hint").textContent = text.hint;
  byId("auth-submit").textContent = text.submit;
  auth.elements.password.autocomplete = text.autocomplete;
}

for (const tab of auth.querySelectorAll(".tab")) {
  tab.addEventListener("click", () => setAuthMode(tab.dataset.mode));
}

auth.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!auth.reportValidity()) return;
  run(byId("auth-submit"), async () => {
    const result = await api("/auth/" + authMode, "POST", Object.fromEntries(new FormData(auth)));
    token = result.access_token;
    sessionStorage.setItem("alacena-token", token);
    auth.reset();
    view();
    notify(authMode === "register" ? "¡Cuenta creada! Empieza agregando ingredientes." : "Sesión iniciada.");
    await Promise.all([loadIngredients(), loadRecipes()]);
  });
});

/* ---------- Inventario ---------- */
function resetIngredient() {
  editing = null;
  ingredient.reset();
  byId("save-ingredient").textContent = "Agregar ingrediente";
  byId("cancel").hidden = true;
  for (const row of byId("ingredients").querySelectorAll(".editing")) row.classList.remove("editing");
}

function formatQuantity(value) {
  return Number(value).toLocaleString("es-CO", { maximumFractionDigits: 3 });
}

async function loadIngredients() {
  const activeToken = token;
  const items = await api("/ingredients");
  if (token !== activeToken) return;
  const list = byId("ingredients");
  list.replaceChildren();
  byId("stat-ingredients").textContent = items.length;
  if (!items.length) list.append(emptyState("🧺", "Tu inventario está vacío. Agrega tu primer ingrediente.", "li"));
  for (const item of items) {
    const row = element("li");
    if (editing === item.id) row.classList.add("editing");
    row.append(
      element("span", item.name, "name"),
      element("span", formatQuantity(item.quantity) + " " + item.unit, "qty"),
      action("✏️", () => {
        resetIngredient();
        editing = item.id;
        row.classList.add("editing");
        for (const field of ["name", "quantity", "unit"]) ingredient.elements[field].value = item[field];
        byId("save-ingredient").textContent = "Guardar cambios";
        byId("cancel").hidden = false;
        ingredient.elements.name.focus();
      }, "ghost icon", "Editar " + item.name),
      action("🗑️", async () => {
        await api("/ingredients/" + item.id, "DELETE");
        if (editing === item.id) resetIngredient();
        await loadIngredients();
        notify(item.name + " eliminado del inventario.");
      }, "danger icon", "Eliminar " + item.name),
    );
    list.append(row);
  }
}

ingredient.addEventListener("submit", (event) => {
  event.preventDefault();
  run(byId("save-ingredient"), async () => {
    const values = Object.fromEntries(new FormData(ingredient));
    values.quantity = Number(values.quantity);
    const wasEditing = editing;
    await api(editing ? "/ingredients/" + editing : "/ingredients", editing ? "PUT" : "POST", values);
    resetIngredient();
    await loadIngredients();
    notify(wasEditing ? "Ingrediente actualizado." : "Ingrediente agregado.");
    ingredient.elements.name.focus();
  });
});

/* ---------- Recetas ---------- */
function updateRecipeStats(recipes) {
  byId("stat-recipes").textContent = recipes.length;
  const rated = recipes.filter((recipe) => recipe.stars);
  byId("stat-rating").textContent = rated.length
    ? (rated.reduce((sum, recipe) => sum + recipe.stars, 0) / rated.length).toFixed(1) + " ★"
    : "–";
}

function starRating(recipe, onChange) {
  const box = element("div", "", "stars");
  box.setAttribute("role", "group");
  box.setAttribute("aria-label", "Calificación");
  box.append(element("span", recipe.stars ? "Tu calificación" : "Califica", "label"));
  const paint = (value) => {
    box.querySelectorAll(".star").forEach((star, index) => star.classList.toggle("on", index < value));
  };
  for (let stars = 1; stars <= 5; stars++) {
    const star = action("★", async () => {
      const updated = await api("/recipes/" + recipe.id + "/rating", "PUT", { stars });
      recipe.stars = updated.stars;
      paint(recipe.stars);
      box.querySelector(".label").textContent = "Tu calificación";
      onChange();
      notify("Calificación guardada: " + stars + (stars === 1 ? " estrella." : " estrellas."));
    }, "star", stars + (stars === 1 ? " estrella" : " estrellas"));
    box.append(star);
  }
  paint(recipe.stars || 0);
  return box;
}

async function loadRecipes() {
  const activeToken = token;
  const recipes = await api("/recipes");
  if (token !== activeToken) return;
  const list = byId("recipes");
  list.replaceChildren();
  updateRecipeStats(recipes);
  if (!recipes.length) list.append(emptyState("📖", "Aún no tienes recetas. Agrega ingredientes y pulsa «Generar receta»."));
  for (const recipe of recipes) {
    const card = element("article", "", "recipe");

    const head = element("div", "", "recipe-head");
    const meta = element("div", "", "meta");
    const date = new Date(recipe.created_at).toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "numeric" });
    meta.append(
      element("span", "⏱ " + recipe.tiempo_minutos + " min", "badge"),
      element("span", "Dificultad " + recipe.dificultad, "badge " + recipe.dificultad),
      element("span", "📅 " + date, "badge"),
    );
    head.append(element("h3", recipe.titulo), meta);

    const body = element("div", "", "recipe-body");
    const used = element("ul");
    const steps = element("ol");
    for (const item of recipe.ingredientes) used.append(element("li", item));
    for (const step of recipe.pasos) steps.append(element("li", step));
    const left = element("div");
    const right = element("div");
    left.append(element("h4", "Ingredientes"), used);
    right.append(element("h4", "Preparación"), steps);
    body.append(left, right);

    const foot = element("div", "", "recipe-foot");
    foot.append(
      starRating(recipe, () => updateRecipeStats(recipes)),
      action("🗑️ Eliminar", async () => {
        if (!window.confirm("¿Eliminar «" + recipe.titulo + "» del historial?")) return;
        await api("/recipes/" + recipe.id, "DELETE");
        await loadRecipes();
        notify("Receta eliminada.");
      }, "danger", "Eliminar receta"),
    );

    card.append(head, body, foot);
    list.append(card);
  }
}

generate.addEventListener("click", () => run(generate, async () => {
  const activeToken = token;
  const label = generate.querySelector(".label");
  generate.classList.add("loading");
  label.textContent = "Cocinando una idea…";
  try {
    await api("/recipes/generate", "POST");
    if (token !== activeToken) return;
    await loadRecipes();
    notify("Receta generada y guardada en tu historial.");
  } finally {
    generate.classList.remove("loading");
    label.textContent = "✨ Generar receta";
  }
}));

byId("cancel").addEventListener("click", resetIngredient);
byId("logout").addEventListener("click", () => { logout(); notify("Sesión cerrada."); });
setAuthMode("login");
view();
if (token) Promise.all([loadIngredients(), loadRecipes()]).catch((error) => notify(error.message, true));
