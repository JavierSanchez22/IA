using System;

namespace ejemploPerceptronXOR
{
    class Program
    {
        static int Activacion(double x)
        {
            return x > 0 ? 1 : 0;
        }

        static void Main(string[] args)
        {
            int[,] datos = {{0,0,0}, {0,1,1}, {1,0,1}, {1,1,0}};

            Random aleatorio = new Random();

            double[] w1 = { aleatorio.NextDouble(), aleatorio.NextDouble(), aleatorio.NextDouble() };
            double[] w2 = { aleatorio.NextDouble(), aleatorio.NextDouble(), aleatorio.NextDouble() };

            double[] wOut = { aleatorio.NextDouble(), aleatorio.NextDouble(), aleatorio.NextDouble() };

            bool aprendizaje = true;
            int epocas = 0;

            int maxEpocas = 10000;

            while (aprendizaje && epocas < maxEpocas)
            {
                aprendizaje = false;

                for (int i = 0; i < 4; i++)
                {
                    int x1 = datos[i, 0];
                    int x2 = datos[i, 1];

                    int h1 = Activacion(x1 * w1[0] + x2 * w1[1] + w1[2]);
                    int h2 = Activacion(x1 * w2[0] + x2 * w2[1] + w2[2]);

                    int salida = Activacion(h1 * wOut[0] + h2 * wOut[1] + wOut[2]);

                    if (salida != datos[i, 2])
                    {
                        w1[0] += aleatorio.NextDouble() - 0.5;
                        w1[1] += aleatorio.NextDouble() - 0.5;
                        w1[2] += aleatorio.NextDouble() - 0.5;

                        w2[0] += aleatorio.NextDouble() - 0.5;
                        w2[1] += aleatorio.NextDouble() - 0.5;
                        w2[2] += aleatorio.NextDouble() - 0.5;

                        wOut[0] += aleatorio.NextDouble() - 0.5;
                        wOut[1] += aleatorio.NextDouble() - 0.5;
                        wOut[2] += aleatorio.NextDouble() - 0.5;

                        aprendizaje = true;
                    }
                }

                epocas++;
            }
            for (int i = 0; i < 4; i++)
            {
                int x1 = datos[i, 0];
                int x2 = datos[i, 1];

                int h1 = Activacion(x1 * w1[0] + x2 * w1[1] + w1[2]);
                int h2 = Activacion(x1 * w2[0] + x2 * w2[1] + w2[2]);

                int salida = Activacion(h1 * wOut[0] + h2 * wOut[1] + wOut[2]);

                Console.WriteLine($"{x1} XOR {x2} = {salida}");
            }

            Console.WriteLine($"Epocas: {epocas}");
        }
    }
}