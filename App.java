import javafx.animation.*;
import javafx.application.Application;
import javafx.geometry.Pos;
import javafx.scene.Group;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.effect.PerspectiveTransform;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.layout.*;
import javafx.stage.Stage;
import javafx.util.Duration;

public class App extends Application {

    private PerspectiveTransform pt = new PerspectiveTransform();
    private VBox mainHUD;

    @Override
    public void start(Stage stage) {

        // =========================
        // BACKGROUND
        // =========================
        Image bgImage = new Image(getClass().getResourceAsStream("/SpectacularTerminal.png"));
        ImageView bgView = new ImageView(bgImage);
        bgView.setPreserveRatio(true);
        bgView.setFitWidth(1200);

        // =========================
        // HEADER
        // =========================
        Label header = new Label("SPECTACULAR TERMINAL");
        header.getStyleClass().add("terminal-text");

        // =========================
        // EXPLANATION (TYPEWRITER TARGET)
        // =========================
        Label explanation = new Label("");
        explanation.getStyleClass().add("terminal-text");
        explanation.setWrapText(true);
        explanation.setMaxWidth(500);

        String explanationText =
                "ALIGNMENT TEST: ENTER A PROMPT OR TOPIC TO TEST HOW THE SELECTED LLMS OF YOUR CHOICE RESPOND UNDER ADVERSARIAL CONDITIONS.\n\n" +
                "YOUR INPUT IS TRANSFORMED INTO A COMPLEX ADVERSARIAL QUESTION FOR MODEL EVALUATION.";

        // =========================
        // PROMPT INPUT
        // =========================
        HBox promptContainer = new HBox(10);
        promptContainer.setAlignment(Pos.CENTER);

        Label promptLabel = new Label("Q:");
        promptLabel.getStyleClass().add("terminal-text");

        TextField promptInput = new TextField();
        promptInput.getStyleClass().add("terminal-input");
        promptInput.setPrefWidth(350);

        promptContainer.getChildren().addAll(promptLabel, promptInput);

        // =========================
        // MAIN HUD
        // =========================
        mainHUD = new VBox(40);
        mainHUD.setAlignment(Pos.CENTER);
        mainHUD.getChildren().addAll(header, explanation, promptContainer);

        // =========================
        // SCANLINES
        // =========================
        Region scanlines = new Region();
        scanlines.getStyleClass().add("glass-overlay");
        scanlines.setMouseTransparent(true);

        // =========================
        // WARP GROUP
        // =========================
        Group warpGroup = new Group(mainHUD, scanlines);
        warpGroup.setEffect(pt);

        // =========================
        // ROOT
        // =========================
        StackPane root = new StackPane();
        root.getChildren().addAll(bgView, warpGroup);

        Scene scene = new Scene(root, 1200, 800);
        scene.getStylesheets().add(getClass().getResource("/style.css").toExternalForm());

        // =========================
        // RESPONSIVE SIZING
        // =========================
        mainHUD.prefWidthProperty().bind(scene.widthProperty().multiply(0.5));
        mainHUD.prefHeightProperty().bind(scene.heightProperty().multiply(0.5));

        scanlines.prefWidthProperty().bind(mainHUD.prefWidthProperty());
        scanlines.prefHeightProperty().bind(mainHUD.prefHeightProperty());

        // =========================
        // CRT CURVATURE
        // =========================
        applyCRTCurve(scene);

        scene.widthProperty().addListener((obs, o, n) -> applyCRTCurve(scene));
        scene.heightProperty().addListener((obs, o, n) -> applyCRTCurve(scene));

        // =========================
        // WARP
        // =========================
        scene.widthProperty().addListener((obs, o, n) -> updateWarp(scene));
        scene.heightProperty().addListener((obs, o, n) -> updateWarp(scene));

        updateWarp(scene);

        // =========================
        // POSITION
        // =========================
        warpGroup.setTranslateX(112);
        warpGroup.setTranslateY(-5);

        // =========================
        // FLICKER
        // =========================
        FadeTransition flicker = new FadeTransition(Duration.millis(70), warpGroup);
        flicker.setFromValue(1.0);
        flicker.setToValue(0.92);
        flicker.setCycleCount(Animation.INDEFINITE);
        flicker.setAutoReverse(true);
        flicker.play();

        // =========================
        // SHOW
        // =========================
        stage.setTitle("Spectacular Terminal - Diagnostic Mode");
        stage.setScene(scene);
        stage.show();

        // =========================
        // TYPEWRITER START
        // =========================
        typeText(explanation, explanationText, 18);
    }

    // =========================================================
    // TYPEWRITER EFFECT
    // =========================================================
    private void typeText(Label label, String fullText, int speedMs) {

        label.setText("");

        final int[] index = {0};

        Timeline timeline = new Timeline(
                new KeyFrame(Duration.millis(speedMs), e -> {
                    if (index[0] < fullText.length()) {
                        label.setText(fullText.substring(0, index[0] + 1));
                        index[0]++;
                    }
                })
        );

        timeline.setCycleCount(fullText.length());
        timeline.play();
    }

    // =========================================================
    // CRT CURVATURE
    // =========================================================
    private void applyCRTCurve(Scene scene) {

        double height = scene.getHeight();
        double centerY = height / 2;

        mainHUD.applyCss();
        mainHUD.layout();

        mainHUD.getChildren().forEach(node -> {

            double nodeY = node.getLayoutY() + 40;
            double dist = (nodeY - centerY) / centerY;

            double curve = 0.06;
            double scale = 1 - curve * (dist * dist);

            node.setScaleX(1.0 + (scale - 1) * 0.6);
            node.setScaleY(1.0 + (scale - 1) * 0.6);

            double bend = dist * dist * 12;
            node.setTranslateX(dist > 0 ? -bend : bend);
        });
    }

    // =========================================================
    // WARP
    // =========================================================
    private void updateWarp(Scene scene) {

        double w = scene.getWidth() * 0.5;
        double h = scene.getHeight() * 0.55;
        double ind = 20;

        pt.setUlx(ind);
        pt.setUly(ind);

        pt.setUrx(w - ind);
        pt.setUry(ind);

        pt.setLlx(0);
        pt.setLly(h);

        pt.setLrx(w);
        pt.setLry(h);
    }

    public static void main(String[] args) {
        launch();
    }
}