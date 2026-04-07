import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
from collections import deque

# ---------------- LOAD MODEL ---------------
model = tf.keras.models.load_model("sign_model.h5")
labels = np.load("labels.npy")

# ---------------- MEDIAPIPE ----------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)

# ---------------- SENTENCE LOGIC ----------------
prediction_buffer = deque(maxlen=15)
last_committed = ""
current_word = ""
sentence = ""

# ---------------- COMMAND LOGIC ----------------
space_counter = 0
del_counter = 0

CONF_THRESHOLD = 0.80     # ML confidence threshold
HOLD_FRAMES = 25          # frames to confirm SPACE / DEL

# ---------------- FINGER COUNT FUNCTION ----------------
def count_fingers(hand_landmarks):
    fingers = []

    # Thumb (x-axis)
    fingers.append(
        1 if hand_landmarks.landmark[4].x >
             hand_landmarks.landmark[3].x else 0
    )

    # Other fingers (y-axis)
    tips = [8, 12, 16, 20]
    joints = [6, 10, 14, 18]

    for tip, joint in zip(tips, joints):
        fingers.append(
            1 if hand_landmarks.landmark[tip].y <
                 hand_landmarks.landmark[joint].y else 0
        )

    return sum(fingers)

# ---------------- MAIN LOOP ----------------
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    predicted_sign = ""

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            features = []
            for lm in hand_landmarks.landmark:
                features.extend([lm.x, lm.y])

            features = np.array(features).reshape(1, -1)
            prediction = model.predict(features, verbose=0)

            probs = prediction[0]
            confidence = np.max(probs)
            predicted_sign = labels[np.argmax(probs)]

            finger_count = count_fingers(hand_landmarks)

            # -------- SAFE COMMAND OVERRIDE --------
            if finger_count == 5 and confidence < CONF_THRESHOLD:
                space_counter += 1
                del_counter = 0
            elif finger_count == 0 and confidence < CONF_THRESHOLD:
                del_counter += 1
                space_counter = 0
            else:
                space_counter = 0
                del_counter = 0

            if space_counter > HOLD_FRAMES:
                predicted_sign = "SPACE"
                space_counter = 0

            elif del_counter > HOLD_FRAMES:
                predicted_sign = "DEL"
                del_counter = 0

            mp_draw.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
            )

    # -------- STABILITY CHECK --------
    if predicted_sign != "":
        prediction_buffer.append(predicted_sign)

        if len(prediction_buffer) == prediction_buffer.maxlen:
            if all(p == prediction_buffer[0] for p in prediction_buffer):
                stable = prediction_buffer[0]

                if stable != last_committed:
                    last_committed = stable

                    if stable == "SPACE":
                        if current_word != "":
                            sentence += current_word + " "
                            current_word = ""

                    elif stable == "DEL":
                        current_word = current_word[:-1]

                    else:
                        current_word += stable

                    prediction_buffer.clear()

    # -------- DISPLAY --------
    cv2.putText(frame, f"Letter: {last_committed}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 255), 2)

    cv2.putText(frame, f"Word: {current_word}",
                (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (255, 0, 0), 2)

    cv2.putText(frame, f"Sentence: {sentence}",
                (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 0), 2)

    cv2.imshow("Sign Language to Sentence", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
