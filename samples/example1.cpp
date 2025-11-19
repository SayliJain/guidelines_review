#include <iostream>
#include <vector>
#include <string>
#include <thread>
#include <mutex>
#include <map>

using namespace std;  // bad: using namespace in global scope

#define maxCount 10            // bad: macro name not UPPERCASE
#define PI_value 3.14159       // bad: naming + magic number
#define SQUARE(X) (X * X)      // bad: macro params not lowercase, missing parens

int Global_count = 0;          // bad: global, naming style
static int ModuleStatic = 5;   // bad: camelCase vs spec, magic number

enum colorMode              // bad: enum name not PascalCase
{
    red,                    // bad: enumerator not UPPERCASE, vague
    GREEN_COLOR,            // inconsistent naming
    blue_value              // bad: not UPPERCASE
};

struct Config                // should be POD but members not initialized
{
    int Port;               // bad: PascalCase, uninitialized
    string HostName;        // bad: PascalCase, uninitialized
    bool useSSL;            // uninitialized
};

class data_manager           // bad: class name not PascalCase
{
public:
    int *rawBuffer;         // bad: raw pointer ownership
    size_t size;            // uninitialized

    data_manager(int sz)    // bad: not explicit, no member init list for all
    {
        size = sz;          // not using brace init
        rawBuffer = new int[sz];   // raw new
        for (int i = 0; i < sz; i++)
        {
            rawBuffer[i] = i * 2;  // magic numbers, no const
        }
    }

    void PrintData()        // bad: PascalCase, not camelCase
    {
        for (int i = 0; i < size; i++) // C-style loop, could use range-for
        {
            cout << "Val: " << rawBuffer[i] << endl;
        }
    }

    void DoSomethingNonConst()
    {
        cout << "ModuleStatic: " << ModuleStatic << endl;
    }
    // no destructor -> memory leak, no RAII, no Rule of Five
};

std::mutex globalMutex;      // global mutex

void WorkerThread(int ID, data_manager &dm, Config cfg)  // bad: param naming, pass-by-value cfg
{
    for (int i = 0; i < maxCount; i++)    // macro name + magic semantics
    {
        std::lock_guard<std::mutex> lock(globalMutex);  // ok pattern, but global mutex
        Global_count += 1;             // bad: global mutation
        cout << "Worker " << ID << " iteration " << i
             << " host=" << cfg.HostName
             << " port=" << cfg.Port
             << " useSSL=" << cfg.useSSL
             << endl;
        if (Global_count > 50)         // magic number
        {
            cout << "High load warning!" << endl;
        }
    }
}

int calculateTotal(int A, int B, int C, int D)   // too many params, PascalCase params
{
    int Result = A + B + C + D;                  // bad: PascalCase local
    if (Result > 100)                            // magic number
    {
        cout << "Large total: " << Result << endl;
    }
    return Result;
}

int main()
{
    cout << "Starting bad-style demo..." << endl;

    Config cfg;                 // members uninitialized
    cfg.Port = 8080;            // magic number, naming style
    cfg.HostName = "localhost"; // no std::string_view, naming style
    cfg.useSSL = true;          // ok but mixed style

    data_manager dm(10);        // raw pointer usage
    dm.PrintData();

    std::vector<int> nums;      // used but not reserved
    for (int i = 0; i < 20; i++)  // magic number, C-style loop
    {
        nums.push_back(i * 3);    // magic number, could use emplace
    }

    std::map<string, int> nameToScore;  // might trigger container rules
    nameToScore["alice"] = 90;          // magic numbers
    nameToScore["bob"] = 75;

    int total = calculateTotal(1, 2, 3, 4);  // magic numbers, no const, etc.
    cout << "Total: " << total << endl;

    std::thread t1(WorkerThread, 1, std::ref(dm), cfg);  // copies cfg
    std::thread t2(WorkerThread, 2, std::ref(dm), cfg);

    t1.join();
    t2.join();

    cout << "Global_count = " << Global_count << endl;

    // forgot: delete[] dm.rawBuffer;  // leak!

    return 0;
}
