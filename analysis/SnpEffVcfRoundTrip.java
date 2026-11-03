import org.snpeff.fileIterator.VcfFileIterator;
import org.snpeff.vcf.VcfEntry;

/** Exercise the native 5.1d VCF parser and serializer without an annotation database. */
public class SnpEffVcfRoundTrip {
    public static void main(String[] args) {
        VcfFileIterator input = new VcfFileIterator(args[0]);
        input.setCreateChromos(true);
        for (VcfEntry entry : input) {
            System.out.println(entry.toString());
        }
    }
}
