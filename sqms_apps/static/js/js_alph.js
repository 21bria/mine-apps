document.addEventListener("alpine:init", () => {
  // main section
  Alpine.data("scrollToTop", () => ({
    showTopButton: false,
    init() {
      window.onscroll = () => {
        this.scrollFunction();
      };
    },

    scrollFunction() {
      if (
        document.body.scrollTop > 50 ||
        document.documentElement.scrollTop > 50
      ) {
        this.showTopButton = true;
      } else {
        this.showTopButton = false;
      }
    },

    goToTop() {
      document.body.scrollTop = 0;
      document.documentElement.scrollTop = 0;
    },
  }));

  // theme customization
  Alpine.data("customizer", () => ({
    showCustomizer: false,
  }));

  // sidebar section
  Alpine.data("sidebar", () => ({
    init() {
      const selector = document.querySelector(
        '.sidebar ul a[href="' + window.location.pathname + '"]'
      );
      if (selector) {
        selector.classList.add("active");
        const ul = selector.closest("ul.sub-menu");
        if (ul) {
          let ele = ul.closest("li.menu").querySelectorAll(".nav-link");
          if (ele) {
            ele = ele[0];
            setTimeout(() => {
              ele.click();
            });
          }
        }
      }
    },
  }));

  // header section
  Alpine.data("header", () => ({
    init() {
      // Ambil URL dari window global
      this.loadNotifications(window.notificationUrl);

      // Set interval untuk memanggil loadNotifications setiap 30 detik
      setInterval(() => {
        this.loadNotifications(window.notificationUrl);
      }, 30000); // 30 detik = 30000 ms
    },

    notifications: [],

    loadNotifications(url) {
      fetch(url)
        .then((response) => {
          if (!response.ok) throw new Error("Failed to fetch notifications");
          return response.json();
        })
        .then((data) => {
          const notifications = data.notifications || [];
          this.notifications = notifications.map((notif) => ({
            id: notif.id,
            message: `<strong>${notif.workflow_title}</strong>: ${notif.message}`,
            time: notif.created_at,
          }));
        })
        .catch((error) => {
          console.error("Error fetching notifications:", error);
        });
    },

    removeNotification(value) {
      this.notifications = this.notifications.filter((d) => d.id !== value);
    },

    removeMessage(value) {
      this.messages = this.messages.filter((d) => d.id !== value);
    },
  }));
});
