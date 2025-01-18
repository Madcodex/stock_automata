#include<stdio.h>

int main()
{
    int a, b, sum;
    char symbol;
    scanf("%d",&a);
    scanf("%d",&b);
    printf("for Addition + and multiplication *");
    
    scanf("%c",&symbol);

    if (symbol== '+')
        sum = a + b;
    else
        sum = a * b;

    printf("%d",sum);
}