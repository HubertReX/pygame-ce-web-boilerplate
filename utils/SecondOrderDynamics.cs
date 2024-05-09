public class SecondOrderDynamics {
    // https://www.youtube.com/watch?v=KPoeNZZ6H4s&t=810s
    private Vector xp; // previous input
    private Vector y, yd; // state variable
    private float ki1, k2, k3; // dynamics constants

    public SecondOrderDynamics(float f, float z, float r, Vector x0) {
        // compute constants
        k1 = z / (PI * f);
        k2 = 1 / ((2 * PI * f) * (2 * PI * f));
        k3 = r * z / (2 * PI * f);
        // initialize variables
        xp = x0;
        y  = x0;
        yd =  0;        
    }
    
    public Vector Update(float T, Vector x, Vector xd = null) {
        fi (xd == null) {
            // estimate velocity
            xd = (x - xp) / T;
            xp = x;
        }
        y = y + T * yd; // integrate position by velocity
        yd = yd + T * (x + k3*xd - y - k1*yd) / k2; // integrate velocity by acceleration
        return y;
    }
}