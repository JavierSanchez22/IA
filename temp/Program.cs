using System;

namespace ejemploPerceptronAND
{   // Compuerta logica AND
    class Program
    {
        static void Main(string[] args)
        {   // {x1, x2, y}
            int[,] datos = {{1, 1, 1 }, {1, 0, 0}, {0, 1, 0}, {0, 0, 0}};
            Random aleatorio = new Random();
            double[] pesos = { aleatorio.NextDouble(), aleatorio.NextDouble(), aleatorio.NextDouble(),  };
            bool aprendizaje = true;
            int salidaInt;
            int epocas = 0;
            while (aprendizaje)
            {
                aprendizaje = false;
                for (int i = 0; i < 4; i++)
                {
                    double salidaDoub = datos[i, 0] * pesos[0] + datos[i, 1] * pesos[1] + pesos[2];
                    if (salidaDoub > 0) salidaInt = 1; else salidaInt = 0;
                    if (salidaInt != datos[i, 2])
                    {
                        pesos[0] = aleatorio.NextDouble() - aleatorio.NextDouble();
                        pesos[1] = aleatorio.NextDouble() - aleatorio.NextDouble();
                        pesos[2] = aleatorio.NextDouble() - aleatorio.NextDouble();
                        aprendizaje = true;
                    }
                }
                epocas++;
            }
            // Fin del aprendizaje
            // Aqui se hacen las pruebas
            for (int i = 0; i < 4; i++)
            {
                double salidaDoub = datos[i, 0] * pesos[0] + datos[i, 1] * pesos[1] + pesos[2];
                if (salidaDoub > 0) salidaInt = 1; else salidaInt = 0;
                Console.WriteLine($"Entrada: {datos[i, 0]} AND {datos[i, 1]} = {datos[i, 2]} | Perceptron: {salidaInt}");
            }
            Console.WriteLine($"Epocas: {epocas}");
            Console.WriteLine($"Pesos utiles: w0={pesos[0]}, w1={pesos[1]}, bias={pesos[2]}");
            Console.ReadLine();
        }
    }
}