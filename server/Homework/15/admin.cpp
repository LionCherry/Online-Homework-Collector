#include <cstdio>
using namespace std;

typedef struct Node{
    int a;
    Node *next;
    Node(int a):a(a),next(0){}
}Node;
typedef Node* Link;
void func(Link &L){
    if(L && L->next && L->next->next){
        Node *P = L;
        while(P->next)
            P = P->next;
        P->next = L;
        L = L->next->next;
        P->next->next->next = 0;
    }
}
void debug(Link L){
    Node *p = L;
    while(p){
        printf("%d -> ", p->a);
        p = p->next;
    }
    putchar(10);
}
int main(){
    Node* p;
    Link L = new Node(1);
    p = L->next = new Node(2);
    p = p->next = new Node(3);
    debug(L);
    func(L);
    debug(L);
    return 0;
}