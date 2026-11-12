_CPP_HEADER = """\
#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <thread>
#include <memory>
#include <cstring>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <type_traits>

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #pragma comment(lib, "ws2_32.lib")
  #define CLOSE_SOCK closesocket
#else
  #include <sys/socket.h>
  #include <arpa/inet.h>
  #include <unistd.h>
  #define CLOSE_SOCK close
#endif

// Helper para Random nativo
double random_val() { return (double)rand() / RAND_MAX; }

// Helper para Input
std::string input() {
    std::string s;
    std::getline(std::cin, s);
    return s;
}

std::string input(const std::string& prompt) {
    std::cout << prompt;
    return input();
}

// Converte linha com inteiros separados por espaco em vetor (ex.: "10 -3 80")
std::vector<double> __parse_ints(const std::string& s) {
    std::vector<double> result;
    std::istringstream iss(s);
    double n;
    while (iss >> n) {
        result.push_back(n);
    }
    return result;
}

std::vector<int> __minipar_range(int end) {
    std::vector<int> values;
    for (int i = 0; i < end; ++i) values.push_back(i);
    return values;
}

std::vector<int> __minipar_range(int start, int end) {
    std::vector<int> values;
    for (int i = start; i < end; ++i) values.push_back(i);
    return values;
}

// Helper para Arrays (.pop) do Python
template<typename T>
auto __array_pop(std::vector<T>& v) {
    if (v.empty()) return T{};
    auto val = v.back();
    v.pop_back();
    return val;
}

// Helper para formatar e printar std::vector (arrays e matrizes) nativamente
template <typename T>
std::ostream& operator<<(std::ostream& os, const std::vector<T>& v) {
    os << "[";
    for (size_t i = 0; i < v.size(); ++i) {
        os << v[i];
        if (i != v.size() - 1) os << ", ";
    }
    os << "]";
    return os;
}

template<typename T>
std::string __to_string(const T& val) {
    if constexpr (std::is_constructible_v<std::string, T>) {
        return std::string(val);
    } else {
        return std::to_string(val);
    }
}

template<typename T>
auto __make_matrix(int rows, int cols, T init_val) {
    using ActualT = std::conditional_t<std::is_same_v<std::decay_t<T>, const char*>, std::string, T>;
    return std::vector<std::vector<ActualT>>(rows, std::vector<ActualT>(cols, init_val));
}

class MiniParChannel {
public:
    std::string ip;
    int port;

    MiniParChannel(std::string ip, int port) : ip(ip), port(port) {}

    void sendData(std::string msg) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) return;
        struct sockaddr_in serv_addr;
        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(port);
        inet_pton(AF_INET, ip.c_str(), &serv_addr.sin_addr);
        
        for(int i=0; i<50; i++) {
            if (connect(sock, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) >= 0) {
                send(sock, msg.c_str(), msg.length(), 0);
                break;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        CLOSE_SOCK(sock);
    }

    std::string receiveData() {
        int server_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (server_fd < 0) return "";
        int opt = 1;
        setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));
        
        struct sockaddr_in address;
        address.sin_family = AF_INET;
        address.sin_addr.s_addr = INADDR_ANY;
        address.sin_port = htons(port);
        
        if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) { CLOSE_SOCK(server_fd); return ""; }
        if (listen(server_fd, 3) < 0) { CLOSE_SOCK(server_fd); return ""; }
        
        int new_socket = accept(server_fd, nullptr, nullptr);
        if (new_socket < 0) { CLOSE_SOCK(server_fd); return ""; }
        
        char buffer[4096] = {0};
        recv(new_socket, buffer, 4096, 0);
        std::string result(buffer);
        
        CLOSE_SOCK(new_socket);
        CLOSE_SOCK(server_fd);
        return result;
    }
};

"""
