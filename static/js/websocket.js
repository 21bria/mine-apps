// document.addEventListener("DOMContentLoaded", function () {
//   // Menentukan grup berdasarkan peran pengguna (misalnya, asisten, manajer, atau admin)
//   const userRole = document.getElementById("user-role").value; // Mengambil peran pengguna dari halaman

//   // Menentukan URL WebSocket yang sesuai berdasarkan peran pengguna
//   const socketUrl = "wss://" + window.location.host + "/ws/" + userRole + "/";

//   // Membuat koneksi WebSocket
//   const socket = new WebSocket(socketUrl);

//   socket.onopen = function (event) {
//     console.log("WebSocket connected to " + socketUrl);
//   };

//   // Ketika menerima pesan
//   socket.onmessage = function (event) {
//     const data = JSON.parse(event.data); // Pastikan data yang diterima berbentuk JSON
//     Swal.fire({
//       title: "Notifikasi Baru!",
//       text: data.message, // Menampilkan pesan notifikasi dari server
//       icon: "info",
//       timer: 3000, // Durasi notifikasi (dalam milidetik)
//       toast: true, // Mengaktifkan toast
//       position: "top-end", // Posisi notifikasi
//       showConfirmButton: false, // Tidak ada tombol konfirmasi
//     });
//   };

//   // Jika WebSocket ditutup
//   socket.onclose = function (event) {
//     console.error("WebSocket closed unexpectedly");
//   };

//   // Jika terjadi error pada WebSocket
//   socket.onerror = function (event) {
//     console.error("WebSocket error: ", event);
//   };
// });
