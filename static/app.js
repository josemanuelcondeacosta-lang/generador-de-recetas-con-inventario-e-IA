const byId = (id) => document.getElementById(id);
const auth = byId("auth");
const ingredient = byId("ingredient");
const generate = byId("generate");
let token = sessionStorage.getItem("alacena-token");
let editing = null;

function notify(message = "", error = false) {
  const status = byId("message");
  status.textContent = message;
  status.hidden = !message;
  status.classList.toggle("error", error);
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
  const result = await response.json();
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
  notify();
  try { await task(); }
  catch (error) { notify(error.message, true); }
  finally { control.disabled = false; }
}

function element(tag, text = "") {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
}

function action(label, task) {
  const button = element("button", label);
  button.className = "secondary";
  button.type = "button";
  button.addEventListener("click", () => run(button, task));
  return button;
}

function resetIngredient() {
  editing = null;
  ingredient.reset();
  byId("save-ingredient").textContent = "Agregar ingrediente";
  byId("cancel").hidden = true;
}

async function loadIngredients() {
  const activeToken = token;
  const items = await api("/ingredients");
  if (token !== activeToken) return;
  const list = byId("ingredients");
  list.replaceChildren();
  if (!items.length) list.append(element("li", "Tu inventario está vacío."));
  for (const item of items) {
    const row = element("li");
    row.append(
      element("span", item.name + " · " + item.quantity + " " + item.unit),
      action("Editar", () => {
        editing = item.id;
        for (const field of ["name", "quantity", "unit"]) ingredient.elements[field].value = item[field];
        byId("save-ingredient").textContent = "Guardar cambios";
        byId("cancel").hidden = false;
        ingredient.elements.name.focus();
      }),
      action("Eliminar", async () => {
        await api("/ingredients/" + item.id, "DELETE");
        if (editing === item.id) resetIngredient();
        await loadIngredients();
      }),
    );
    list.append(row);
  }
}

async function loadRecipes() {
  const activeToken = token;
  const recipes = await api("/recipes");
  if (token !== activeToken) return;
  const list = byId("recipes");
  list.replaceChildren();
  if (!recipes.length) list.append(element("p", "Aquí aparecerán tus recetas generadas."));
  for (const recipe of recipes) {
    const card = element("article");
    const used = element("ul");
    const steps = element("ol");
    for (const item of recipe.ingredientes) used.append(element("li", item));
    for (const step of recipe.pasos) steps.append(element("li", step));
    const label = element("label", "Calificación");
    const select = element("select");
    select.append(new Option("Elige estrellas", "", false, !recipe.stars));
    for (let stars = 1; stars <= 5; stars++) {
      select.append(new Option(stars + (stars === 1 ? " estrella" : " estrellas"), stars, false, recipe.stars === stars));
    }
    label.append(select);
    const row = element("div");
    row.className = "rating";
    row.append(label, action("Guardar", async () => {
      if (!select.value) throw new Error("Elige una calificación de 1 a 5.");
      await api("/recipes/" + recipe.id + "/rating", "PUT", { stars: Number(select.value) });
      notify("Calificación guardada.");
    }), action("Eliminar receta", async () => {
      if (!window.confirm("¿Eliminar esta receta del historial?")) return;
      await api("/recipes/" + recipe.id, "DELETE");
      await loadRecipes();
    }));
    card.append(element("h3", recipe.titulo), element("p", recipe.tiempo_minutos + " min · " + recipe.dificultad),
      element("strong", "Ingredientes"), used, element("strong", "Preparación"), steps, row);
    list.append(card);
  }
}

auth.addEventListener("submit", (event) => {
  event.preventDefault();
  const control = event.submitter || auth.querySelector("button");
  run(control, async () => {
    const result = await api("/auth/" + control.value, "POST", Object.fromEntries(new FormData(auth)));
    token = result.access_token;
    sessionStorage.setItem("alacena-token", token);
    auth.reset();
    view();
    await Promise.all([loadIngredients(), loadRecipes()]);
  });
});

ingredient.addEventListener("submit", (event) => {
  event.preventDefault();
  run(byId("save-ingredient"), async () => {
    const values = Object.fromEntries(new FormData(ingredient));
    values.quantity = Number(values.quantity);
    await api(editing ? "/ingredients/" + editing : "/ingredients", editing ? "PUT" : "POST", values);
    resetIngredient();
    await loadIngredients();
  });
});

generate.addEventListener("click", () => run(generate, async () => {
  const activeToken = token;
  generate.textContent = "Generando…";
  try {
    await api("/recipes/generate", "POST");
    if (token !== activeToken) return;
    await loadRecipes();
    notify("Receta guardada en tu historial.");
  } finally { generate.textContent = "Generar receta"; }
}));
byId("cancel").addEventListener("click", resetIngredient);
byId("logout").addEventListener("click", () => { logout(); notify(); });
view();
if (token) Promise.all([loadIngredients(), loadRecipes()]).catch((error) => notify(error.message, true));
