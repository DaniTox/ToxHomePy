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

const char* ERRIN = "{ \"error\" : \"Struttura messaggio non valida\" }";

int readOnlyPins[7] = {};
int pinsIndex = 0;


