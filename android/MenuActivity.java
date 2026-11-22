package fr.battleref.menutest;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputFilter;
import android.text.InputType;
import android.util.LruCache;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class MenuActivity extends Activity {
    private static final int GOLD = 0xffecc47a;
    private static final int INK = 0xfffff0d8;
    private static final int MUTED = 0xffb4b6b3;
    private static final int PANEL = 0xff17272d;
    private static final int EDGE = 0xff8a7556;
    private static final int HEALTH = 0xffffaaa0;
    private static final int SHIELD = 0xff9ce2ec;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final LruCache<String, Bitmap> images = new LruCache<String, Bitmap>(12 * 1024 * 1024) {
        @Override
        protected int sizeOf(String key, Bitmap bitmap) {
            return bitmap.getAllocationByteCount();
        }
    };
    private final Runnable ticker = new Runnable() {
        @Override
        public void run() {
            poll();
            handler.postDelayed(this, 80);
        }
    };
    private PyObject bridge;
    private JSONObject catalogue;
    private JSONObject state;
    private FrameLayout root;
    private LinearLayout content;
    private HorizontalScrollView handScroll;
    private String screen = "home";
    private String mode = "";
    private String address = "";
    private String notice = "";
    private String startupError = "";
    private int selected = -1;
    private boolean pending;
    private int scrollX;

    @Override
    protected void onCreate(Bundle savedState) {
        super.onCreate(savedState);
        getWindow().setStatusBarColor(PANEL);
        getWindow().setNavigationBarColor(PANEL);
        home();
        new Thread(this::loadGame, "battle-catalogue").start();
        handler.post(ticker);
    }

    private void loadGame() {
        try {
            File data = new File(getFilesDir(), "battle-data");
            copyAssets("data", data);
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(getApplicationContext()));
            }
            PyObject loaded = Python.getInstance().getModule("battle_bridge")
                    .callAttr("BattleBridge", data.getAbsolutePath());
            JSONObject cards = new JSONObject(loaded.callAttr("cards").toString());
            handler.post(() -> {
                if (isDestroyed()) return;
                bridge = loaded;
                catalogue = cards;
                if (screen.equals("home")) home();
            });
        } catch (Exception error) {
            android.util.Log.e("BattleRef", "Chargement du jeu", error);
            handler.post(() -> {
                if (isDestroyed()) return;
                startupError = "Impossible de charger le jeu.";
                if (screen.equals("home")) home();
            });
        }
    }

    private void copyAssets(String source, File destination) throws IOException {
        String[] entries = getAssets().list(source);
        if (entries != null && entries.length > 0) {
            if (!destination.mkdirs() && !destination.isDirectory()) throw new IOException(source);
            for (String entry : entries) copyAssets(source + "/" + entry, new File(destination, entry));
        } else {
            try (InputStream input = getAssets().open(source); FileOutputStream output = new FileOutputStream(destination)) {
                byte[] bytes = new byte[8192];
                int count;
                while ((count = input.read(bytes)) != -1) output.write(bytes, 0, count);
            }
        }
    }

    private int dp(float units) {
        return Math.round(units * getResources().getDisplayMetrics().density);
    }

    private GradientDrawable panel(int fill, int edge, int radius) {
        GradientDrawable background = new GradientDrawable();
        background.setColor(fill);
        background.setCornerRadius(dp(radius));
        background.setStroke(dp(1), edge);
        return background;
    }

    private Bitmap bitmap(String path) {
        if (path.isEmpty()) return null;
        Bitmap cached = images.get(path);
        if (cached != null) return cached;
        try (InputStream input = getAssets().open(path)) {
            BitmapFactory.Options options = new BitmapFactory.Options();
            if (path.startsWith("asset/image/")) options.inSampleSize = 2;
            Bitmap decoded = BitmapFactory.decodeStream(input, null, options);
            if (decoded != null) images.put(path, decoded);
            return decoded;
        } catch (IOException error) {
            return null;
        }
    }

    private void canvas(String name) {
        screen = name;
        root = new FrameLayout(this);
        root.setBackgroundColor(PANEL);
        ImageView backdrop = new ImageView(this);
        backdrop.setImageBitmap(bitmap("asset/board/theatre-des-echos.webp"));
        backdrop.setScaleType(ImageView.ScaleType.CENTER_CROP);
        backdrop.setColorFilter(0xa409151b);
        root.addView(backdrop, new FrameLayout.LayoutParams(-1, -1));
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(14), dp(8), dp(14), dp(10));
        root.addView(content, new FrameLayout.LayoutParams(-1, -1));
        setContentView(root);
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                    insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets.consumeSystemWindowInsets();
        });
        root.requestApplyInsets();
    }

    private TextView label(String text, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(color);
        view.setTextSize(size);
        view.setGravity(Gravity.CENTER);
        if (bold) view.setTypeface(null, Typeface.BOLD);
        return view;
    }

    private Button button(String text, boolean enabled, Runnable callback) {
        Button view = new Button(this);
        view.setAllCaps(false);
        view.setText(text);
        view.setTextSize(15);
        view.setTextColor(enabled ? INK : MUTED);
        view.setBackground(panel(enabled ? PANEL : 0xff223034, enabled ? GOLD : EDGE, 10));
        view.setEnabled(enabled);
        view.setOnClickListener(ignored -> callback.run());
        return view;
    }

    private void addButton(String text, boolean enabled, Runnable callback) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, dp(50));
        params.topMargin = dp(10);
        content.addView(button(text, enabled, callback), params);
    }

    private void spacer() {
        content.addView(new View(this), new LinearLayout.LayoutParams(1, 0, 1));
    }

    private void home() {
        canvas("home");
        spacer();
        content.addView(label("BATTLE REF", 48, INK, true));
        content.addView(label("ARENA", 22, GOLD, true));
        spacer();
        addButton("Jouer", bridge != null, () -> play(""));
        if (bridge == null) {
            content.addView(label(startupError.isEmpty() ? "Chargement…" : startupError, 16, INK, false));
        }
        spacer();
    }

    private void play(String message) {
        if (bridge != null) bridge.callAttr("close");
        handScroll = null;
        state = null;
        scrollX = 0;
        selected = -1;
        pending = false;
        notice = "";
        canvas("play");
        addButton("Retour", true, this::home);
        spacer();
        content.addView(label("Jouer", 32, INK, true));
        addButton("Solo", true, () -> start("solo", ""));
        addButton("Créer une partie", true, this::chooseInterface);
        addButton("Rejoindre une partie", true, this::joinForm);
        if (!message.isEmpty()) {
            TextView feedback = label(message, 16, GOLD, false);
            feedback.setPadding(0, dp(14), 0, 0);
            content.addView(feedback);
        }
        spacer();
    }

    private void chooseInterface() {
        List<String> addresses = new ArrayList<>();
        try {
            for (NetworkInterface adapter : Collections.list(NetworkInterface.getNetworkInterfaces())) {
                if (!adapter.isUp() || adapter.isLoopback()) continue;
                for (InetAddress ip : Collections.list(adapter.getInetAddresses())) {
                    if (ip instanceof Inet4Address && !ip.isLinkLocalAddress()) addresses.add(ip.getHostAddress());
                }
            }
        } catch (SocketException error) {
            play("Impossible de lire l’adresse du réseau.");
            return;
        }
        Collections.sort(addresses);
        if (addresses.isEmpty()) {
            play("Connectez-vous à un réseau Wi-Fi.");
        } else if (addresses.size() == 1) {
            start("host", addresses.get(0));
        } else {
            canvas("interface");
            addButton("Annuler", true, () -> play(""));
            spacer();
            content.addView(label("Adresse de cet appareil", 24, INK, true));
            for (String ip : addresses) addButton(ip, true, () -> start("host", ip));
            spacer();
        }
    }

    private void joinForm() {
        canvas("joinForm");
        addButton("Annuler", true, () -> play(""));
        spacer();
        content.addView(label("Adresse IPv4 de l’hôte", 23, INK, true));
        EditText input = new EditText(this);
        input.setText(address);
        input.setHint("192.168.1.20");
        input.setSingleLine();
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        input.setFilters(new InputFilter[]{new InputFilter.LengthFilter(15)});
        input.setImeOptions(EditorInfo.IME_ACTION_GO);
        input.setTextColor(INK);
        input.setHintTextColor(MUTED);
        input.setContentDescription("Adresse IPv4 de l’hôte");
        content.addView(input, new LinearLayout.LayoutParams(-1, dp(55)));
        Runnable connect = () -> {
            address = input.getText().toString().trim();
            ((InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE))
                    .hideSoftInputFromWindow(input.getWindowToken(), 0);
            start("join", address);
        };
        input.setOnEditorActionListener((view, action, event) -> {
            if (action != EditorInfo.IME_ACTION_GO) return false;
            connect.run();
            return true;
        });
        addButton("Se connecter", true, connect);
        spacer();
    }

    private void start(String newMode, String host) {
        mode = newMode;
        bridge.callAttr("start", mode, host);
        waiting(mode.equals("host") ? "Ouverture de la partie…" : "Connexion…", "");
    }

    private void waiting(String title, String host) {
        canvas("waiting");
        addButton("Annuler", true, () -> play(""));
        spacer();
        content.addView(label(title, 24, INK, true));
        if (!host.isEmpty()) {
            TextView ip = label(host, 34, GOLD, true);
            ip.setTextIsSelectable(true);
            content.addView(ip);
            content.addView(label("Indiquez cette adresse à l’autre joueur sur le même Wi-Fi.", 16, INK, false));
        }
        spacer();
    }

    private void poll() {
        if (bridge == null || (!screen.equals("battle") && !screen.equals("waiting"))) return;
        try {
            JSONArray events = new JSONArray(bridge.callAttr("poll").toString());
            boolean redraw = false;
            for (int index = 0; index < events.length(); index++) {
                JSONObject event = events.getJSONObject(index);
                switch (event.getString("type")) {
                    case "waiting":
                        waiting("En attente d’un joueur", event.getJSONObject("value").getString("address"));
                        break;
                    case "state":
                        state = event.getJSONObject("value");
                        selected = -1;
                        pending = false;
                        notice = "";
                        redraw = true;
                        break;
                    case "error":
                        pending = false;
                        notice = event.getString("value");
                        redraw = true;
                        break;
                    case "closed":
                        if (state == null || state.isNull("result")) {
                            play(event.getString("value"));
                            return;
                        }
                        break;
                }
            }
            if (redraw && state != null) battle();
        } catch (JSONException error) {
            android.util.Log.e("BattleRef", "État de partie invalide", error);
            play("État de partie illisible.");
        }
    }

    private boolean canAct() {
        return state != null && state.isNull("result") && state.optInt("active") == state.optInt("seat") && !pending;
    }

    private JSONObject player(int seat) {
        return state.optJSONArray("players").optJSONObject(seat - 1);
    }

    private boolean isTarget(int seat, Integer slot) {
        if (!canAct() || selected == -1) return false;
        JSONArray targets = state.optJSONArray("targets").optJSONArray(selected);
        for (int index = 0; index < targets.length(); index++) {
            JSONArray pair = targets.optJSONArray(index);
            if (pair.optInt(0) == seat && (slot == null ? pair.isNull(1) : pair.optInt(1, -1) == slot)) return true;
        }
        return false;
    }

    private void submit(String kind, int target, Integer slot) {
        if (!canAct()) return;
        try {
            JSONObject action = new JSONObject();
            action.put("type", kind);
            action.put("revision", state.optInt("revision"));
            if (kind.equals("play")) {
                action.put("card", selected);
                action.put("target", target);
                action.put("slot", slot == null ? JSONObject.NULL : slot);
            }
            pending = true;
            bridge.callAttr("submit", action.toString());
            battle();
        } catch (JSONException error) {
            pending = false;
            notice = "Action illisible.";
            battle();
        }
    }

    private void battle() {
        if (handScroll != null) scrollX = handScroll.getScrollX();
        canvas("battle");
        int own = state.optInt("seat");
        int opponent = 3 - own;
        LinearLayout header = new LinearLayout(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.addView(button("Menu", true, () -> play("")), new LinearLayout.LayoutParams(dp(76), dp(44)));
        header.addView(new View(this), new LinearLayout.LayoutParams(0, 1, 1));
        header.addView(button("Passer", canAct(), () -> submit("pass", 0, null)), new LinearLayout.LayoutParams(dp(100), dp(44)));
        content.addView(header, new LinearLayout.LayoutParams(-1, dp(46)));

        addPlayer(opponent, mode.equals("solo") ? "Bot" : "Adversaire");
        addTerrain(opponent);
        String status = state.optInt("active") == own ? "Votre tour" : "Tour adverse";
        if (!state.isNull("result")) {
            status = state.optString("result").equals("draw") ? "Match nul" :
                    state.optInt("result") == own ? "Victoire" : "Défaite";
        } else {
            status += "  ·  Tour " + state.optInt("turn");
        }
        content.addView(label(status, 19, GOLD, true), new LinearLayout.LayoutParams(-1, dp(29)));
        content.addView(label(notice, 13, INK, false), new LinearLayout.LayoutParams(-1, dp(22)));
        addTerrain(own);
        addPlayer(own, "Vous");
        addHand();

        LinearLayout footer = new LinearLayout(this);
        footer.setGravity(Gravity.CENTER_VERTICAL);
        String energy = "Énergie  " + player(own).optInt("energy") + " / " + state.optInt("max_energy");
        footer.addView(label(energy, 15, INK, true), new LinearLayout.LayoutParams(0, -1, 1));
        String draw = "Piocher · " + state.optInt("draw_cost");
        footer.addView(button(draw, canAct() && state.optBoolean("can_draw"), () -> submit("draw", 0, null)),
                new LinearLayout.LayoutParams(0, dp(44), 1));
        content.addView(footer, new LinearLayout.LayoutParams(-1, dp(46)));
    }

    private void addPlayer(int seat, String name) {
        JSONObject player = player(seat);
        boolean target = isTarget(seat, null);
        String text = name + "  ·  " + player.optInt("hp") + " PV";
        if (seat != state.optInt("seat")) {
            text += "\n" + player.optInt("hand_count") + " en main  ·  " + player.optInt("deck_count") + " en pioche";
        }
        TextView plate = label(text, 15, HEALTH, true);
        plate.setBackground(panel(0xe617272d, target ? GOLD : EDGE, 9));
        if (target) plate.setOnClickListener(view -> submit("play", seat, null));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, dp(seat == state.optInt("seat") ? 29 : 43));
        params.topMargin = dp(3);
        params.bottomMargin = dp(3);
        content.addView(plate, params);
    }

    private void addTerrain(int seat) {
        LinearLayout row = new LinearLayout(this);
        JSONArray slots = player(seat).optJSONArray("slots");
        for (int index = 0; index < slots.length(); index++) {
            final int slot = index;
            JSONObject unit = slots.optJSONObject(index);
            boolean target = isTarget(seat, index);
            View card = unit == null ? label("◇", 21, target ? GOLD : EDGE, false) :
                    card(unit.optString("id"), unit, target);
            if (unit == null) card.setBackground(panel(0xb80b191e, target ? GOLD : EDGE, 8));
            if (target) card.setOnClickListener(view -> submit("play", seat, slot));
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, -1, 1);
            params.setMargins(dp(3), dp(2), dp(3), dp(2));
            row.addView(card, params);
        }
        content.addView(row, new LinearLayout.LayoutParams(-1, 0, 1));
    }

    private void addHand() {
        handScroll = new HorizontalScrollView(this);
        handScroll.setFillViewport(false);
        handScroll.setHorizontalScrollBarEnabled(true);
        LinearLayout hand = new LinearLayout(this);
        JSONArray cards = state.optJSONArray("hand");
        for (int index = 0; index < cards.length(); index++) {
            final int cardIndex = index;
            View card = card(cards.optString(index), null, selected == index);
            card.setOnClickListener(view -> {
                if (!canAct()) return;
                selected = selected == cardIndex ? -1 : cardIndex;
                notice = selected == -1 ? "" : state.optJSONArray("targets").optJSONArray(selected).length() > 0 ?
                        "Choisissez une cible" : "Cette carte ne peut pas être jouée.";
                battle();
            });
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(dp(101), -1);
            params.setMargins(dp(3), dp(3), dp(3), dp(4));
            hand.addView(card, params);
        }
        handScroll.addView(hand, new FrameLayout.LayoutParams(-2, -1));
        content.addView(handScroll, new LinearLayout.LayoutParams(-1, dp(115)));
        HorizontalScrollView displayed = handScroll;
        int restore = scrollX;
        displayed.post(() -> displayed.scrollTo(restore, 0));
    }

    private View card(String id, JSONObject unit, boolean highlight) {
        JSONObject info = catalogue.optJSONObject(id);
        if (info == null) return label(id, 13, INK, false);
        boolean character = info.optString("type").equals("character");
        LinearLayout card = new LinearLayout(this);
        card.setPadding(dp(3), dp(2), dp(3), dp(2));
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackground(panel(character ? 0xff2b2631 : 0xff3f2629, highlight ? GOLD : EDGE, 8));

        LinearLayout badges = new LinearLayout(this);
        TextView cost = label(info.optString("cost"), 12, SHIELD, true);
        cost.setContentDescription("Coût " + info.optString("cost"));
        badges.addView(cost, new LinearLayout.LayoutParams(dp(20), -1));
        TextView name = label(info.optString("name"), 10, INK, true);
        name.setMaxLines(2);
        badges.addView(name, new LinearLayout.LayoutParams(0, -1, 1));
        if (character) {
            int hp = unit == null ? info.optInt("hp") : unit.optInt("hp");
            TextView health = label(Integer.toString(hp), 12, HEALTH, true);
            health.setContentDescription(hp + " PV");
            badges.addView(health, new LinearLayout.LayoutParams(dp(20), -1));
        }
        card.addView(badges, new LinearLayout.LayoutParams(-1, dp(30)));

        ImageView art = new ImageView(this);
        art.setImageBitmap(bitmap(info.optString("image", "")));
        art.setScaleType(ImageView.ScaleType.CENTER_CROP);
        card.addView(art, new LinearLayout.LayoutParams(-1, 0, 1));
        String description = "";
        if (character) {
            if (unit != null && unit.optInt("shield") > 0) description = "Bouclier " + unit.optInt("shield");
        } else {
            String effect = info.optString("effect");
            description = (effect.equals("attack") ? "Attaque" : effect.equals("heal") ? "Soin" : "Bouclier")
                    + " " + info.optInt("amount");
        }
        if (!description.isEmpty()) card.addView(label(description, 11, INK, false));
        return card;
    }

    @Override
    public void onBackPressed() {
        if (screen.equals("home")) super.onBackPressed();
        else if (screen.equals("play")) home();
        else play("");
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        if (bridge != null) bridge.callAttr("close");
        super.onDestroy();
    }
}
