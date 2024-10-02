public class Main {
    public static Student[] students;
    public static int studentCount;

    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("Usage: java Main <studentCount> <studentFile>");
            return;
        }
        studentCount = Integer.parseInt(args[1]);
    }
}