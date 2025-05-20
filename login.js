const app = Vue.createApp({
  data() {
    return {
      username: "",
      loginError: false
    };
  },

  methods: {
    async login() {
      if (!this.username.trim()) {
        this.loginError = true;
        return;
      }

      try {
        await axios.post("http://127.0.0.1:5000/api/login", {
          username: this.username.trim()
        });
        localStorage.setItem("username", this.username.trim());
        window.location.href = "index.html";
      } catch (err) {
        this.loginError = true;
      }
    }
  },

  mounted() {
    // 可選：自動 focus 或清除 username
    // this.username = "";
  }
});

app.mount("#app");