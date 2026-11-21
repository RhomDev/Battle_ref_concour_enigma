const { cards, media, synergies } = window.BATTLE_REF_PREVIEW;
const catalogue = new Map(cards.map(card => [card.id, card]));
const mediaRegistry = new Map(media.map(item => [item.id, item]));
const amplifications = new Map(synergies.filter(item => item.amplification).map(item => [item.sourceCardId, item]));
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
const drawCost = 1;
const otis = catalogue.get("otis");
const ymca = catalogue.get("ymca");
const otisCombo = synergies.find(item => item.event === "characters_combined" && item.sourceCardId === otis.id);
const steps = [
  { label: `Piocher · ${drawCost} ⚡`, cost: drawCost, run: drawCard },
  { label: `Déployer ${otis.name} · ${otis.cost} ⚡`, cost: otis.cost, cardId: otis.id, run: deployOtis },
  { label: `Jouer ${ymca.name} · ${ymca.cost} ⚡`, cost: ymca.cost, cardId: ymca.id, run: playRef },
  { label: "Terminer le tour", cost: 0, run: finishTurn },
];
let state;
let audio;

function node(tag, className, label) {
  const element = document.createElement(tag);
  element.className = className;
  if (label !== undefined) element.textContent = label;
  return element;
}

function renderCard(card, { compact = false, interactive = false, hp, shield, guard, amplified } = {}) {
  const element = node(interactive ? "button" : "div", `card ${card.kind}`);
  if (interactive) {
    element.type = "button";
    const details = [`${card.name}, ${card.kind === "ref" ? "Ref" : "Personnage"}`, `coût ${card.cost}`];
    if (card.stats) details.push(`${hp ?? card.stats.hp} PV`);
    if (shield) details.push(`${shield} Bouclier`);
    if (guard) details.push("Garde");
    if (amplified) details.push("amplifiée");
    element.setAttribute("aria-label", details.join(", "));
    element.setAttribute("aria-haspopup", "dialog");
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
    element.append(node("span", "card-copy card-stat card-hp", `♥ ${hp ?? card.stats.hp}`));
  }
  if (shield) {
    const marker = node("span", "card-copy card-status", `◈ ${shield}`);
    marker.title = `Bouclier ${shield}`;
    element.append(marker);
  }
  if (guard) element.append(node("span", "card-copy card-stat card-guard", "Garde"));
  if (compact && amplified) {
    element.dataset.amplified = true;
    element.append(node("span", "card-copy card-stat card-amplified", "Amplifiée"));
  }
  return { element, photo };
}

function placeCards(container, positions, compact) {
  container.replaceChildren();
  for (const position of positions) {
    const slot = node("div", "slot");
    if (position) {
      const { id, ...values } = position;
      const inHand = container === dom.main;
      const amplified = inHand && Boolean(findAlly(amplifications.get(id)?.requirements[0].cardId));
      const { element } = renderCard(catalogue.get(id), { compact, interactive: true, amplified, ...values });
      element.dataset.next = inHand && steps[state.step]?.cardId === id;
      element.addEventListener("click", () => {
        inspectCard(id, values, inHand, amplified);
        dom.inspector.showModal();
      });
      slot.append(element);
    }
    container.append(slot);
  }
}

function inspectCard(id, values, inHand, amplified) {
  const card = catalogue.get(id);
  const { element, photo } = renderCard(card, values);
  const display = node("div", "detail-card");
  display.append(element);
  dom.detail.replaceChildren(display);
  const amplifier = amplifications.get(id);
  if (amplifier) {
    const partner = catalogue.get(amplifier.requirements[0].cardId);
    const label = amplified ? `Amplification active · ${partner.name}` : `Personnage associé · ${partner.name}`;
    dom.detail.append(node("p", "detail-note", label));
  }
  if (photo) {
    dom.detail.append(node("p", "detail-note", photo.caption ?? photo.restrictions.split(". ")[0] + "."));
  }
  const step = steps[state.step];
  const canUse = inHand && step?.cardId === id && state.energy >= step.cost;
  dom["activate-card"].hidden = !canUse;
  if (canUse) dom["activate-card"].textContent = step.label;
}

function renderScene() {
  const step = steps[state.step];
  dom.energy.textContent = state.energy;
  energyGems.forEach((gem, index) => gem.classList.toggle("charged", index < state.energy));
  placeCards(dom.ennemi, state.enemy, true);
  placeCards(dom.allie, state.ally, true);
  placeCards(dom.main, state.hand.map(id => ({ id })), true);
  dom.activate.textContent = step?.label ?? "Rejouer la scène";
  dom.activate.disabled = Boolean(step && state.energy < step.cost);
}

function reset() {
  const vegeta = catalogue.get("vegeta");
  const protection = vegeta.abilities[0].effects;
  state = {
    step: 0,
    energy: energyGems.length,
    enemy: [{ id: "creeper" }, null, {
      id: vegeta.id,
      hp: vegeta.stats.hp,
      shield: protection.find(effect => effect.op === "shield").amount,
      guard: protection.some(effect => effect.op === "guard"),
    }],
    ally: [{ id: "perceval", shield: catalogue.get("perceval").abilities[0].effects[0].amount }, null, { id: "trump", shield: 0 }],
    hand: [ymca.id, "perlimpinpin", "sss_plendide"],
  };
  renderScene();
  announce("Votre tour", "Perceval et Trump sont déjà déployés. Piochez pour ajouter un Personnage à votre main.");
  battle.querySelectorAll(".signal-mote").forEach(mote => mote.remove());
}

function findAlly(id) {
  return state.ally.find(position => position && position.id === id);
}

function announce(title, message) {
  dom.event.replaceChildren(node("strong", "", title), node("span", "", message));
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

function drawCard() {
  state.hand.push(otis.id);
  renderScene();
  announce(`${otis.name} rejoint votre main`, `La pioche coûte ${drawCost} ⚡. Déployez ${otis.name} aux côtés de Perceval.`);
}

function deployOtis() {
  const guard = otis.abilities[0].effects.some(effect => effect.op === "guard");
  const partner = findAlly(otisCombo.requirements[0].cardId);
  const shield = partner ? otisCombo.effects[0].amount : 0;
  state.hand = state.hand.filter(id => id !== otis.id);
  state.ally[1] = { id: otis.id, shield, guard };
  renderScene();
  announce(otisCombo.title, `Otis gagne Garde et ${shield} Bouclier avec Perceval. Il peut protéger votre camp.`);
  playSound();
}

function playRef() {
  const amplification = amplifications.get(ymca.id);
  const amplifier = findAlly(amplification.requirements[0].cardId);
  const baseDamage = ymca.abilities[0].effects[0].amount;
  const bonusDamage = amplifier ? amplification.effects[0].amount : 0;
  const target = state.enemy.find(position => position?.guard);
  const absorbed = Math.min(target.shield, baseDamage + bonusDamage);
  const source = dom.main.querySelector(`[data-card-id="${ymca.id}"]`).getBoundingClientRect();

  target.shield -= absorbed;
  target.hp -= baseDamage + bonusDamage - absorbed;
  state.hand = state.hand.filter(id => id !== ymca.id);
  if (amplifier && ymca.tags.includes("dance")) {
    const danceEffect = catalogue.get(amplifier.id).abilities.find(ability => ability.timing === "ally_dance_ref_resolved");
    amplifier.shield += danceEffect.effects[0].amount;
  }
  renderScene();
  const defender = dom.ennemi.querySelector(`[data-card-id="${target.id}"]`);
  defender.classList.add("flash");
  animateSignal(source, defender);
  announce(amplification.title, `${ymca.name} inflige ${baseDamage} + ${bonusDamage} dégâts. La Garde de Vegeta protège son camp et son Bouclier en absorbe ${absorbed}. Vegeta garde ${target.hp} PV.`);
  playSound();
}

function finishTurn() {
  renderScene();
  announce("Fin du tour", "Otis protège votre camp. La Ref a touché Vegeta et les PV du joueur adverse sont intacts.");
}

function advanceScene() {
  const step = steps[state.step];
  if (dom.inspector.open) dom.inspector.close();
  if (!step) {
    reset();
  } else if (state.energy >= step.cost) {
    state.energy -= step.cost;
    state.step += 1;
    step.run();
  }
  dom.activate.focus({ preventScroll: true });
}

dom.activate.addEventListener("click", advanceScene);
dom["activate-card"].addEventListener("click", advanceScene);
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
