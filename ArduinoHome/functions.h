
void handleInput();
void handleNumber(int);

int getobit(int);
int getpin(int);

int* getps();
void sendsts();

void setPinAsReadOnly(int);
bool isReadOnly(int);

bool idDigitalWriteEnabled(int);

const char startOfNumberDelimiter = '<';
const char endOfNumberDelimiter   = '>';

static const uint8_t analog_pins[] = {A0,A1,A2,A3,A4};

const int PINS_N = 14;
const int PINS_AN = 5;

const char* ERRIN = "{ \"error\" : \"Struttura messaggio non valida\" }";

int readOnlyPins[7] = {};
int pinsIndex = 0;

typedef struct ToxObject {
  String className;
} ToxObject;

int16_t dallas(int,byte);

void freeObjectPin(int);
void createCustomObject(int, char*);
void writeHighPin(int);

void printNumberReceived(int);

uint8_t getAnalogPin(int);

void p(String X) {
   for (int i = 0; i < X.length(); i++) {
    char c = X.charAt(i);
    
    if (c < 16) {Serial.print("0");}
    Serial.print(c, HEX);
   }
   Serial.println("");

}

