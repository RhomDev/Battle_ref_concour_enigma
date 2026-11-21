const { cards, media, synergies } = window.BATTLE_REF_PREVIEW;
const catalogue = new Map(cards.map(card => [card.id, card]));
const mediaRegistry = new Map(media.map(item => [item.id, item]));
const categories = { cinema: "Cinéma", series: "Séries", politique: "Politique", anime: "Animé", musique: "Musique", jeu_video: "Jeu vidéo" };
const symbols = { pulse: "◈", subtitle: "…", scroll: "¶", spotlight: "▶", rewind: "⏪", powder: "✦", pixel: "▦" };
const dom = Object.fromEntries(["ennemi", "allie", "main", "detail", "event", "activate", "reset", "energy", "son", "volume", "credit-list", "gallery"].map(id => [id, document.getElementById(id)]));
const handIds = ["perlimpinpin", "danse_jojo", "touche_pas_bulma", "sss_plendide"];
let state;
let audio;

function node(tag, className, label) {
  const element = document.createElement(tag);
  element.className = className;
  if (label !== undefined) element.textContent = label;
  return element;
}

function renderCard(card, { compact = false, interactive = false, hp, shield } = {}) {
  const element = node(interactive ? "button" : "div", `card ${card.kind}`);
  if (interactive) {
    element.type = "button";
    element.setAttribute("aria-label", `${card.name}, ${card.kind === "ref" ? "Ref" : "Personnage"}, coût ${card.cost}${card.stats ? `, attaque ${card.stats.attack}, ${hp ?? card.stats.hp} PV` : ""}`);
    element.setAttribute("aria-pressed", "false");
  }
  element.dataset.compact = compact;
  element.dataset.cardId = card.id;
  element.dataset.longTitle = card.name.length >= 13;
  const artwork = node("span", "card-illustration");
  const photo = card.media.map(id => mediaRegistry.get(id)).find(item => item?.kind === "image" && item.status === "demo_asset");
  if (photo) {
    const picture = node("img", "photo");
    picture.src = photo.localPath;
    picture.alt = "";
    if (photo.focalPoint) {
      const { x, y } = photo.focalPoint;
      artwork.style.setProperty("--focus", `${x}% ${y}%`);
    }
    artwork.append(picture);
  } else {
    const symbol = node("span", "symbol", symbols[card.visual]);
    symbol.setAttribute("aria-hidden", "true");
    artwork.append(symbol);
  }
  const frame = node("img", "card-frame");
  frame.alt = "";
  frame.src = card.kind === "character" ? "assets/frames/personnage.webp" : "assets/frames/ref.webp";

  element.append(
    node("span", "card-base"), artwork, frame,
    node("span", "card-copy card-cost", card.cost),
    node("span", "card-copy card-title", card.name),
    node("span", "card-copy card-tag", card.kind === "ref" ? `Ref · ${categories[card.category]}` : categories[card.category]),
    node("span", "card-copy card-effect", card.text),
  );
  if (card.stats) {
    element.append(
      node("span", "card-copy card-stat card-atk", `⚔ ${card.stats.attack}`),
      node("span", "card-copy card-stat card-hp", `♥ ${hp ?? card.stats.hp}`),
    );
  }
  if (shield) {
    const marker = node("span", "card-copy card-status", `◈ ${shield}`);
    marker.title = `Bouclier ${shield}`;
    if (interactive) element.setAttribute("aria-label", element.getAttribute("aria-label") + `, Bouclier ${shield}`);
    element.append(marker);
  }
  return { element, photo };
}

function placeCards(container, positions, compact) {
  container.replaceChildren();
  for (const position of positions) {
    const slot = node("div", "slot");
    if (position) {
      const { id, ...values } = position;
      const { element } = renderCard(catalogue.get(id), { compact, interactive: true, ...values });
      element.addEventListener("click", () => selectCard(id, values));
      slot.append(element);
    }
    container.append(slot);
  }
}

function selectCard(id, values = {}) {
  const card = catalogue.get(id);
  const { element, photo } = renderCard(card, values);
  state.selected = id;
  const display = node("div", "detail-card");
  display.append(element);
  const description = node("p", "description", card.text);
  const note = node("p", "detail-note", photo ? photo.restrictions.split(". ")[0] + "." : "Visuel provisoire · scène d’origine référencée dans le catalogue.");
  dom.detail.replaceChildren(display, description, note);
  for (const button of document.querySelectorAll("button.card")) {
    const selected = button.dataset.cardId === id;
    button.dataset.selected = selected;
    button.setAttribute("aria-pressed", String(selected));
  }
  dom.activate.disabled = id !== "perlimpinpin" || state.played;
  dom.activate.textContent = state.played ? "Ref jouée" : "Jouer la Ref";
}

function renderScene() {
  dom.energy.textContent = state.played ? 3 : 4;
  placeCards(dom.ennemi, [{ id: "trump", hp: 3, shield: state.played ? 0 : 1 }, { id: "vegeta", hp: 3 }, null], true);
  placeCards(dom.allie, [{ id: "macron" }, { id: "psy", hp: 2 }, null], true);
  const hand = state.played ? [...handIds.slice(1), "ymca"] : handIds;
  placeCards(dom.main, hand.map(id => ({ id })), true);
}

function reset() {
  state = { played: false, selected: null };
  renderScene();
  selectCard("perlimpinpin");
  dom.event.textContent = "Jouez Poudre de perlimpinpin pour dissiper le Bouclier de Trump et découvrir une synergie.";
}

function playSound() {
  if (dom.son.getAttribute("aria-pressed") !== "true" || audio?.state !== "running") return;
  const frequencies = [285, 424, 568];
  const volume = Number(dom.volume.value) / 100;
  for (const [index, frequency] of frequencies.entries()) {
    const start = audio.currentTime + index * 0.055;
    const oscillator = audio.createOscillator();
    const envelope = audio.createGain();
    oscillator.type = "sine";
    oscillator.frequency.value = frequency;
    envelope.gain.setValueAtTime(0, start);
    envelope.gain.linearRampToValueAtTime(0.25 * volume, start + 0.015);
    envelope.gain.linearRampToValueAtTime(0, start + 0.12);
    oscillator.connect(envelope).connect(audio.destination);
    oscillator.start(start);
    oscillator.stop(start + 0.13);
  }
}

dom.son.addEventListener("click", async () => {
  const enabled = dom.son.getAttribute("aria-pressed") !== "true";
  if (enabled) {
    audio ??= new AudioContext();
    try {
      await audio.resume();
    } catch {
      dom.event.textContent = "Le son est bloqué par le navigateur.";
      return;
    }
  }
  dom.son.setAttribute("aria-pressed", String(enabled));
  dom.son.textContent = enabled ? "Couper le son" : "Activer le son";
});

dom.activate.addEventListener("click", () => {
  if (state.played || state.selected !== "perlimpinpin") return;
  state.played = true;
  renderScene();
  selectCard("perlimpinpin");
  const match = synergies.find(synergy => synergy.sourceCardId === "perlimpinpin" && synergy.requirements.some(requirement => requirement.cardId === "macron"));
  dom.event.textContent = `Bouclier dissipé. Synergie révélée · ${match.title}. Vous piochez Y.M.C.A.`;
  dom.detail.querySelector(".card").classList.add("flash");
  dom.ennemi.querySelector('[data-card-id="trump"]').classList.add("flash");
  playSound();
});
dom.reset.addEventListener("click", reset);
const gallery = document.getElementById("catalogue").querySelector("details");
gallery.addEventListener("toggle", () => {
  if (!gallery.open || dom.gallery.childElementCount) return;
  for (const card of cards) {
    const article = node("article", "gallery-item");
    article.append(renderCard(card).element);
    const summary = node("p", "detail-note", card.origin.work);
    article.append(summary);
    dom.gallery.append(article);
  }
});
document.querySelector('a[href="#catalogue"]').addEventListener("click", () => { gallery.open = true; });

for (const photo of media.filter(item => item.status === "demo_asset")) {
  const licenseNames = { "PD-USGov": "domaine public aux États-Unis", "CC0-1.0": "CC0 1.0", "CC-BY-2.0": "CC BY 2.0" };
  const item = node("li", "", `${photo.creator} · ${licenseNames[photo.license]} · `);
  const source = node("a", "", "source de la photographie");
  source.href = photo.sourceUrl;
  item.append(source);
  if (photo.license !== "PD-USGov") {
    const license = node("a", "", "licence");
    license.href = photo.license === "CC0-1.0" ? "https://creativecommons.org/publicdomain/zero/1.0/" : "https://creativecommons.org/licenses/by/2.0/";
    item.append(" · ", license);
  }
  item.append(" · Redimensionnement WebP et cadrage à l’affichage.");
  dom["credit-list"].append(item);
}
reset();
