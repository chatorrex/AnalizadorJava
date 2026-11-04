public class Control {
    static int sumar(int a, int b) {
        return a + b;
    }

    public static void main(String[] args) {
        int contador = sumar(1, 2);
        while (contador > 0) {
            if (contador == 2 || contador == 1) {
                System.out.println("Continúa");
            } else {
                System.out.println(contador);
            }
            contador = contador - 1;
        }
    }
}
