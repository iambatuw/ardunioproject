// Yuz algilandiginda buzzer calan Arduino kodu
// Python'dan gelen '1' -> buzzer ON, '0' -> buzzer OFF
// Pin 8 = Buzzer (+),  GND = Buzzer (-)

const int BUZZER_PIN = 8;

void setup() {
  Serial.begin(9600);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    char gelen = Serial.read();

    if (gelen == '1') {
      // Yuz algilandi -> buzzer ac
      // Aktif buzzer icin: dogrudan HIGH
      digitalWrite(BUZZER_PIN, HIGH);
      // Pasif buzzer kullaniyorsan ust satiri silip alttakini ac:
      // tone(BUZZER_PIN, 1000);
    }
    else if (gelen == '0') {
      // Yuz yok -> sustur
      digitalWrite(BUZZER_PIN, LOW);
      // Pasif buzzer icin:
      // noTone(BUZZER_PIN);
    }
  }
}
