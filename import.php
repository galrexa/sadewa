<?php
// Koneksi ke MySQL
$servername = "localhost";
$username = "root";
$password = "";  // No password
$dbname = "sadewa_db";

$conn = new mysqli($servername, $username, $password, $dbname);

// Cek koneksi
if ($conn->connect_error) {
    die("Koneksi gagal: " . $conn->connect_error);
}

// Path file CSV (sesuaikan jika perlu)
$filename = "drugs.csv";

if (($handle = fopen($filename, "r")) !== FALSE) {
    // Skip header (baris pertama)
    $header = fgetcsv($handle, 1000, ",");  // Delimiter koma

    while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {  // Delimiter koma
        $nama_obat = $data[0];
        $nama_obat_internasional = $data[1];
        $is_active = $data[2];

        // Query INSERT (id, created_at, updated_at auto-generate)
        $sql = "INSERT INTO drugs (nama_obat, nama_obat_internasional, is_active) 
                VALUES ('$nama_obat', '$nama_obat_internasional', $is_active)";

        if ($conn->query($sql) === TRUE) {
            echo "Data '$nama_obat' berhasil diimpor.<br>";
        } else {
            echo "Error: " . $sql . "<br>" . $conn->error . "<br>";
        }
    }
    fclose($handle);
} else {
    echo "File CSV tidak ditemukan!";
}

// Tutup koneksi
$conn->close();
echo "<br>Import selesai. Cek tabel dengan SELECT * FROM drugs;";
?>