const { cards, media, synergies } = window.BATTLE_REF_PREVIEW;
const catalogue = new Map(cards.map(card => [card.id, card]));
const mediaRegistry = new Map(media.map(item => [item.id, item]));
const categories = { cinema: "Cinéma", series: "Séries", politique: "Politique", anime: "Animé", musique: "Musique", jeu_video: "Jeu vidéo" };
const symbols = { pulse: "◈", subtitle: "…", scroll: "¶", spotlight: "▶", rewind: "⏪", powder: "✦", pixel: "▦" };
const licenses = {
  "PD-USGov": { label: "domaine public aux États-Unis" },
  "CC0-1.0": { label: "CC0 1.0", url: "https://creativecommons.org/publicdomain/zero/1.0/" },
  "CC-BY-2.0": { label: "CC BY 2.0", url: "https://creativecommons.org/licenses/by/2.0/" },
  "CC-BY-SA-2.0": { label: "CC BY-SA 2.0", url: "https://creativecommons.org/licenses/by-sa/2.0/" },
};
const dom = Object.fromEntries([
  "ennemi", "allie", "main", "detail", "event", "activate", "activate-card", "reset", "energy",
  "son", "volume", "credit-list", "gallery", "inspector", "catalogue", "options", "show-catalogue",
  "show-options", "fullscreen", "audio-status",
].map(id => [id, document.getElementById(id)]));
const battle = document.querySelector(".battle");
const energyGems = document.querySelectorAll(".energy-gems i");
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

  const title = node("span", "card-copy card-title", card.name);
  title.dataset.long = card.name.length >= 15;
  element.append(
    artwork, frame,
    node("span", "card-copy card-cost", card.cost),
    title,
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
      element.addEventListener("click", () => {
        selectCard(id, values);
        element.focus({ preventScroll: true });
        dom.inspector.showModal();
      });
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
  dom.detail.replaceChildren(display);
  if (photo) {
    dom.detail.append(node("p", "detail-note", photo.caption ?? photo.restrictions.split(". ")[0] + "."));
  }
  for (const button of document.querySelectorAll("button.card")) {
    const selected = button.dataset.cardId === id;
    button.dataset.selected = selected;
    button.setAttribute("aria-pressed", String(selected));
  }
  const canPlay = id === "perlimpinpin" && !state.played;
  dom.activate.disabled = !canPlay && !state.played;
  dom.activate.textContent = state.played ? "Rejouer" : "Jouer la Ref";
  dom["activate-card"].hidden = !canPlay;
  dom["activate-card"].disabled = !canPlay;
}

function renderScene() {
  const energy = state.played ? 3 : 4;
  dom.energy.textContent = energy;
  energyGems.forEach((gem, index) => gem.classList.toggle("charged", index < energy));
  placeCards(dom.ennemi, [{ id: "trump", hp: 3, shield: state.played ? 0 : 1 }, null, { id: "vegeta", hp: 3 }], true);
  placeCards(dom.allie, [{ id: "macron" }, null, { id: "psy", hp: 2 }], true);
  const hand = state.played ? [...handIds.slice(1), "ymca"] : handIds;
  placeCards(dom.main, hand.map(id => ({ id })), true);
}

function reset() {
  state = { played: false, selected: null };
  renderScene();
  selectCard("perlimpinpin");
  dom.event.replaceChildren();
  battle.querySelectorAll(".signal-mote").forEach(mote => mote.remove());
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
    try {
      audio ??= new AudioContext();
      await audio.resume();
    } catch {
      dom["audio-status"].hidden = false;
      return;
    }
  }
  dom["audio-status"].hidden = true;
  dom.son.setAttribute("aria-pressed", String(enabled));
  dom.son.textContent = enabled ? "Couper le son" : "Activer le son";
});

function animateSignal(source, target) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const board = battle.getBoundingClientRect();
  const destination = target.getBoundingClientRect();
  const startX = source.left + source.width / 2 - board.left;
  const startY = source.top + source.height / 2 - board.top;
  const endX = destination.left + destination.width / 2 - board.left;
  const endY = destination.top + destination.height / 2 - board.top;
  for (let index = 0; index < 3; index += 1) {
    const mote = node("span", "signal-mote");
    mote.setAttribute("aria-hidden", "true");
    battle.append(mote);
    const animation = mote.animate([
      { transform: `translate(${startX}px, ${startY}px) scale(.7)`, opacity: 0 },
      { transform: `translate(${(startX + endX) / 2 + 52 + index * 10}px, ${(startY + endY) / 2}px) scale(1)`, opacity: 1 },
      { transform: `translate(${endX}px, ${endY}px) scale(.3)`, opacity: 0 },
    ], { duration: 510 + index * 45, delay: index * 30, easing: "cubic-bezier(.2,.48,.3,1)" });
    animation.finished.then(() => mote.remove(), () => mote.remove());
  }
}

function playRef() {
  if (state.played || state.selected !== "perlimpinpin") return;
  const source = dom.main.querySelector('[data-card-id="perlimpinpin"]').getBoundingClientRect();
  if (dom.inspector.open) dom.inspector.close();
  state.played = true;
  renderScene();
  selectCard("perlimpinpin");
  const match = synergies.find(synergy => synergy.sourceCardId === "perlimpinpin" && synergy.requirements.some(requirement => requirement.cardId === "macron"));
  dom.event.replaceChildren(
    node("strong", "", match.title),
    node("span", "", "Bouclier dissipé · Y.M.C.A. rejoint votre main."),
  );
  const trump = dom.ennemi.querySelector('[data-card-id="trump"]');
  trump.classList.add("flash");
  animateSignal(source, trump);
  dom.activate.focus({ preventScroll: true });
  playSound();
}

dom.activate.addEventListener("click", () => {
  if (state.played) {
    reset();
    return;
  }
  playRef();
});
dom["activate-card"].addEventListener("click", playRef);
dom.reset.addEventListener("click", () => {
  dom.options.close();
  reset();
});

dom["show-catalogue"].addEventListener("click", () => {
  if (!dom.gallery.childElementCount) {
    for (const card of cards) {
      const article = node("article", "gallery-item");
      article.append(renderCard(card).element);
      article.append(node("p", "detail-note", card.origin.work));
      dom.gallery.append(article);
    }
  }
  dom.catalogue.showModal();
});
dom["show-options"].addEventListener("click", () => dom.options.showModal());

if (document.fullscreenEnabled) {
  dom.fullscreen.hidden = false;
  dom.fullscreen.addEventListener("click", async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      dom.fullscreen.title = "Le navigateur refuse le plein écran";
    }
  });
  document.addEventListener("fullscreenchange", () => {
    const label = document.fullscreenElement ? "Quitter le plein écran" : "Plein écran";
    dom.fullscreen.title = label;
    dom.fullscreen.setAttribute("aria-label", label);
  });
}

for (const photo of media.filter(item => item.status === "demo_asset")) {
  const license = licenses[photo.license];
  const item = node("li", "", `${photo.creator} · ${license.label} · `);
  const source = node("a", "", "source de la photographie");
  source.href = photo.sourceUrl;
  item.append(source);
  if (license.url) {
    const terms = node("a", "", "licence");
    terms.href = license.url;
    item.append(" · ", terms);
  }
  item.append(" · Redimensionnement WebP et cadrage à l’affichage.");
  dom["credit-list"].append(item);
}
reset();
