package fr.battleref.menutest;

import android.app.Activity;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.os.Bundle;
import android.widget.ImageView;

import java.io.IOException;
import java.io.InputStream;

public final class MenuActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);

        ImageView menu = new ImageView(this);
        menu.setBackgroundColor(Color.BLACK);
        menu.setScaleType(ImageView.ScaleType.FIT_CENTER);
        menu.setFitsSystemWindows(true);
        try (InputStream image = getAssets().open("menu.png")) {
            menu.setImageBitmap(BitmapFactory.decodeStream(image));
        } catch (IOException error) {
            throw new IllegalStateException("Menu image is missing", error);
        }
        setContentView(menu);
    }
}
