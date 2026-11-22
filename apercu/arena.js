const { cards, media } = window.BATTLE_REF_PREVIEW;
const catalogue = new Map(cards.map(card => [card.id, card]));
const mediaRegistry = new Map(media.map(item => [item.id, item]));
const categories = { cinema: "Cinéma", series: "Séries", politique: "Politique", anime: "Animé", musique: "Musique", jeu_video: "Jeu vidéo", internet: "Internet" };
const symbols = { pulse: "◈", subtitle: "…", scroll: "¶", spotlight: "▶", rewind: "⏪", powder: "✦", pixel: "▦" };
const licenses = {
  "PD-USGov": { label: "domaine public aux États-Unis" },
  "PDM-1.0": { label: "domaine public", url: "https://creativecommons.org/publicdomain/mark/1.0/" },
  "CC0-1.0": { label: "CC0 1.0", url: "https://creativecommons.org/publicdomain/zero/1.0/" },
  "CC-BY-2.0": { label: "CC BY 2.0", url: "https://creativecommons.org/licenses/by/2.0/" },
  "CC-BY-3.0": { label: "CC BY 3.0", url: "https://creativecommons.org/licenses/by/3.0/" },
  "CC-BY-SA-2.0": { label: "CC BY-SA 2.0", url: "https://creativecommons.org/licenses/by-sa/2.0/" },
  "CC-BY-SA-3.0": { label: "CC BY-SA 3.0", url: "https://creativecommons.org/licenses/by-sa/3.0/" },
  "CC-BY-SA-4.0": { label: "CC BY-SA 4.0", url: "https://creativecommons.org/licenses/by-sa/4.0/" },
};
const dom = Object.fromEntries([
  "ennemi", "allie", "main", "detail", "event", "activate", "activate-card", "reset", "energy",
  "son", "volume", "credit-list", "gallery", "inspector", "catalogue", "options", "show-catalogue",
  "show-options", "fullscreen", "audio-status", "projection", "catalogue-search", "catalogue-empty",
].map(id => [id, document.getElementById(id)]));
const battle = document.querySelector(".battle");
const energyGems = document.querySelectorAll(".energy-gems i");
const drawCost = 1;
const macron = catalogue.get("macron");
const ymca = catalogue.get("ymca");
const steps = [
  { label: `Piocher · ${drawCost} ⚡`, cost: drawCost, run: drawCard },
  { label: `Déployer ${macron.name} · ${macron.cost} ⚡`, cost: macron.cost, cardId: macron.id, run: deployMacron },
  { label: `Jouer ${ymca.name} · ${ymca.cost} ⚡`, cost: ymca.cost, cardId: ymca.id, run: playRef },
  { label: "Terminer le tour", cost: 0, run: finishTurn },
];
let state;
let playback;

function cardMedia(card) {
  return card.media.map(id => mediaRegistry.get(id));
}

function localMedia(card, kind) {
  const sources = cardMedia(card);
  const demo = sources.find(item => item.kind === kind && item.status === "demo_asset");
  const original = sources.flatMap(item => (item.localCopies ?? []).map(copy => ({
    ...copy, sourceUrl: item.sourceUrl,
  }))).find(copy => copy.kind === kind);
  return kind === "audio" ? original : demo ?? original;
}

function node(tag, className, label) {
  const element = document.createElement(tag);
  element.className = className;
  if (label !== undefined) element.textContent = label;
  return element;
}

function renderCard(card, { compact = false, interactive = false, hp, shield, amplified } = {}) {
  const element = node(interactive ? "button" : "div", `card ${card.kind}`);
  if (interactive) {
    element.type = "button";
    const details = [`${card.name}, ${card.kind === "ref" ? "Ref" : "Personnage"}`, `coût ${card.cost}`];
    if (card.stats) details.push(`${hp ?? card.stats.hp} PV`);
    if (shield) details.push(`${shield} Bouclier`);
    if (amplified) details.push("amplifiée");
    element.setAttribute("aria-label", details.join(", "));
    element.setAttribute("aria-haspopup", "dialog");
  }
  element.dataset.compact = compact;
  element.dataset.cardId = card.id;
  const artwork = node("span", "card-illustration");
  const photo = localMedia(card, "image");
  if (photo) {
    const picture = node("img", "photo");
    picture.src = `../${photo.localPath}`;
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
  frame.src = card.kind === "character" ? "../asset/frames/personnage.webp" : "../asset/frames/ref.webp";

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
      const card = catalogue.get(id);
      const inHand = container === dom.main;
      const amplified = inHand && Boolean(findAlly(card.synergy?.character_id));
      const { element } = renderCard(card, { compact, interactive: true, amplified, ...values });
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
  if (card.synergy) {
    const { character_id, bonus } = card.synergy;
    const partner = catalogue.get(character_id);
    const label = amplified ? `Amplification active · ${partner.name} (+${bonus})` : `Personnage associé · ${partner.name} (+${bonus})`;
    dom.detail.append(node("p", "detail-note", label));
  }
  if (photo) {
    const credit = node("p", "detail-note");
    const label = photo.caption ?? photo.restrictions.split(". ")[0] + ".";
    credit.append(photo.sourceUrl ? sourceLink(photo, label) : label);
    dom.detail.append(credit);
  }
  const references = cardMedia(card).filter(item => item.status === "reference_only");
  if (references.length) {
    const list = node("ul", "media-sources");
    for (const media of references) {
      const entry = node("li", "");
      entry.append(sourceLink(media, media.caption ?? "Consulter la source originale"));
      for (const copy of media.localCopies ?? []) {
        const formats = { image: "Image locale", audio: "MP3 local", gif: "GIF local", video: "Vidéo locale" };
        const local = sourceLink({ sourceUrl: `../${copy.localPath}`, restrictions: copy.caption }, formats[copy.kind]);
        entry.append(" · ", local);
      }
      list.append(entry);
    }
    dom.detail.append(list);
  }
  const track = localMedia(card, "audio");
  if (track || ((localMedia(card, "gif") || localMedia(card, "video")) && !reducedMotion())) {
    const button = node("button", "metal-button media-preview", "Tester les médias");
    const preview = node("figure", "projection projection-inline");
    button.type = "button";
    preview.hidden = true;
    button.addEventListener("click", () => playCardMedia(card, preview));
    dom.detail.append(button, preview);
    if (track?.caption) dom.detail.append(node("p", "detail-note", track.caption));
  }
  const step = steps[state.step];
  const canUse = inHand && step?.cardId === id && state.energy >= step.cost;
  dom["activate-card"].hidden = !canUse;
  if (canUse) dom["activate-card"].textContent = step.label;
}

function sourceLink(asset, label) {
  const link = node("a", "", label);
  link.href = asset.sourceUrl;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.title = asset.restrictions;
  return link;
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
  stopPlayback();
  const vegeta = catalogue.get("vegeta");
  state = {
    step: 0,
    energy: energyGems.length,
    enemy: [{ id: "creeper" }, null, { id: vegeta.id, hp: vegeta.stats.hp }],
    ally: [{ id: "mista" }, null, { id: "trump" }],
    hand: [ymca.id, "perlimpinpin", "touche_pas_bulma"],
  };
  renderScene();
  announce("Votre tour", "Mista et Trump sont déjà déployés. Piochez pour ajouter un Personnage à votre main.");
  battle.querySelectorAll(".signal-mote").forEach(mote => mote.remove());
}

function findAlly(id) {
  return state.ally.find(position => position && position.id === id);
}

function announce(title, message) {
  dom.event.replaceChildren(node("strong", "", title), node("span", "", message));
}

function reducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function stopPlayback() {
  if (!playback) return;
  const { sound, video, projection, timers } = playback;
  timers.forEach(timer => clearTimeout(timer));
  sound?.pause();
  video?.pause();
  projection.replaceChildren();
  projection.hidden = true;
  playback = undefined;
}

function playCardMedia(card, projection = dom.projection) {
  stopPlayback();
  const animation = reducedMotion() ? undefined : localMedia(card, "gif") ?? localMedia(card, "video");
  const soundEnabled = projection !== dom.projection || dom.son.getAttribute("aria-pressed") === "true";
  const track = soundEnabled ? localMedia(card, "audio") : undefined;
  if (!animation && !track) return false;

  const sound = track ? new Audio(`../${track.localPath}`) : undefined;
  const clip = { sound, projection, timers: [] };
  playback = clip;
  if (animation) {
    const picture = node(animation.kind === "video" ? "video" : "img", "");
    if (animation.kind === "video") {
      clip.video = picture;
      picture.playsInline = true;
      picture.volume = Number(dom.volume.value) / 100;
      picture.muted = Boolean(track) || !soundEnabled;
    } else {
      picture.alt = "";
    }
    projection.replaceChildren(picture, node("figcaption", "", animation.caption ?? card.name));
    projection.hidden = false;
    const hideProjection = () => {
      if (playback !== clip) return;
      clip.video?.pause();
      projection.replaceChildren();
      projection.hidden = true;
    };
    picture.addEventListener(clip.video ? "playing" : "load", () => {
      if (playback === clip) clip.timers.push(setTimeout(hideProjection, animation.durationMs));
    }, { once: true });
    picture.addEventListener("error", hideProjection, { once: true });
    picture.src = `../${animation.localPath}`;
    if (clip.video) clip.video.play().catch(hideProjection);
  }
  if (sound) {
    sound.volume = Number(dom.volume.value) / 100;
    sound.addEventListener("playing", () => {
      if (playback === clip) clip.timers.push(setTimeout(() => sound.pause(), track.durationMs));
    }, { once: true });
    sound.play().catch(() => {
      if (playback === clip) dom["audio-status"].hidden = false;
    });
  }
  return true;
}

dom.son.addEventListener("click", () => {
  const enabled = dom.son.getAttribute("aria-pressed") !== "true";
  dom["audio-status"].hidden = true;
  dom.son.setAttribute("aria-pressed", String(enabled));
  dom.son.textContent = enabled ? "Couper le son" : "Activer le son";
  if (!enabled) {
    playback?.sound?.pause();
    if (playback?.video) playback.video.muted = true;
  }
});

dom.volume.addEventListener("input", () => {
  const volume = Number(dom.volume.value) / 100;
  if (playback?.sound) playback.sound.volume = volume;
  if (playback?.video) playback.video.volume = volume;
});

dom.inspector.addEventListener("close", () => {
  if (playback && playback.projection !== dom.projection) stopPlayback();
});

function animateSignal(source, target) {
  if (reducedMotion()) return;
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
  state.hand.push(macron.id);
  renderScene();
  announce(`${macron.name} rejoint votre main`, `La pioche coûte ${drawCost} ⚡. Déployez ${macron.name} sur la case libre.`);
}

function deployMacron() {
  state.hand = state.hand.filter(id => id !== macron.id);
  state.ally[1] = { id: macron.id };
  renderScene();
  announce("Macron rejoint le plateau", `${ymca.name} est prête à jouer. Trump peut amplifier ses dégâts.`);
}

function playRef() {
  const amplifier = findAlly(ymca.synergy?.character_id);
  const baseDamage = ymca.abilities.effect.amount;
  const bonusDamage = amplifier ? ymca.synergy.bonus : 0;
  const target = state.enemy.find(position => position?.id === "vegeta");
  const damage = baseDamage + bonusDamage;
  const source = dom.main.querySelector(`[data-card-id="${ymca.id}"]`).getBoundingClientRect();

  target.hp = Math.max(0, target.hp - damage);
  state.hand = state.hand.filter(id => id !== ymca.id);
  renderScene();
  const defender = dom.ennemi.querySelector(`[data-card-id="${target.id}"]`);
  defender.classList.add("flash");
  animateSignal(source, defender);
  announce(ymca.name, `${ymca.name} inflige ${damage} dégâts à Vegeta. Il lui reste ${target.hp} PV.`);
  playCardMedia(ymca);
}

function finishTurn() {
  renderScene();
  announce("Fin du tour", "La Ref a touché Vegeta.");
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
      const partnerId = card.synergy?.character_id;
      const partner = catalogue.get(partnerId)?.name ?? "";
      article.dataset.search = searchText(`${card.name} ${card.origin.work} ${categories[card.category]} ${partner}`);
      const { element } = renderCard(card, { interactive: true });
      element.addEventListener("click", () => {
        inspectCard(card.id, {}, false, false);
        dom.inspector.showModal();
      });
      article.append(element);
      article.append(node("p", "detail-note", card.origin.work));
      dom.gallery.append(article);
    }
  }
  dom.catalogue.showModal();
});
function searchText(value) {
  return value.normalize("NFD").replace(/[.\p{Diacritic}]/gu, "").toLocaleLowerCase("fr").trim();
}

dom["catalogue-search"].addEventListener("input", event => {
  const query = searchText(event.target.value);
  let matches = false;
  for (const article of dom.gallery.children) {
    article.hidden = !article.dataset.search.includes(query);
    matches ||= !article.hidden;
  }
  dom["catalogue-empty"].hidden = matches;
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

for (const asset of media.filter(item => item.status === "demo_asset")) {
  const license = licenses[asset.license];
  const item = node("li", "", `${asset.caption ?? asset.kind} · ${asset.creator} · ${license.label}`);
  if (asset.sourceUrl) {
    const source = node("a", "", "source");
    source.href = asset.sourceUrl;
    item.append(" · ", source);
  } else if (asset.sourceNote) {
    item.append(` · ${asset.sourceNote}`);
  }
  if (license.url) {
    const terms = node("a", "", "licence");
    terms.href = license.url;
    item.append(" · ", terms);
  }
  item.append(` · ${asset.restrictions}`);
  dom["credit-list"].append(item);
}
reset();
