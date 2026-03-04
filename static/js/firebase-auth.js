const config = window.FIREBASE_CONFIG;
if (!config || !config.apiKey) {
  console.warn('Firebase config missing. Skipping Firebase auth.');
}

const requireVerified = window.FIREBASE_REQUIRE_EMAIL_VERIFIED === true;

const showMessage = (form, message, isError = true) => {
  if (!form) return;
  const box = form.querySelector('[data-auth-message]');
  if (!box) return;
  box.textContent = message;
  box.classList.remove('hidden');
  box.classList.toggle('text-rose-200', isError);
  box.classList.toggle('text-emerald-200', !isError);
};

const getFieldValue = (form, name) => {
  const input = form.querySelector(`[name="${name}"]`);
  return input ? input.value.trim() : '';
};

const postTokenToBackend = async (idToken) => {
  const csrf = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
  const res = await fetch('/accounts/firebase-login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrf,
    },
    body: JSON.stringify({ id_token: idToken }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Login failed');
  }
};

const init = async () => {
  if (!config || !config.apiKey) return;

  const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js');
  const {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    sendEmailVerification,
    sendPasswordResetEmail,
    signOut,
  } = await import('https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js');

  const app = initializeApp(config);
  const auth = getAuth(app);

  const registerForm = document.querySelector('[data-firebase-auth="register"]');
  if (registerForm) {
    registerForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const email = getFieldValue(registerForm, 'email');
      const password = getFieldValue(registerForm, 'password1');
      const confirm = getFieldValue(registerForm, 'password2');
      if (!email || !password) {
        showMessage(registerForm, 'Email and password are required.');
        return;
      }
      if (password !== confirm) {
        showMessage(registerForm, 'Passwords do not match.');
        return;
      }
      try {
        const cred = await createUserWithEmailAndPassword(auth, email, password);
        await sendEmailVerification(cred.user);
        showMessage(registerForm, 'Verification email sent. Please verify and then log in.', false);
        await signOut(auth);
      } catch (err) {
        showMessage(registerForm, err.message || 'Registration failed.');
      }
    });
  }

  const loginForm = document.querySelector('[data-firebase-auth="login"]');
  if (loginForm) {
    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const email = getFieldValue(loginForm, 'username') || getFieldValue(loginForm, 'email');
      const password = getFieldValue(loginForm, 'password');
      if (!email || !password) {
        showMessage(loginForm, 'Email and password are required.');
        return;
      }
      try {
        const cred = await signInWithEmailAndPassword(auth, email, password);
        if (requireVerified && !cred.user.emailVerified) {
          await sendEmailVerification(cred.user);
          showMessage(loginForm, 'Please verify your email. We sent a new verification link.', true);
          await signOut(auth);
          return;
        }
        const idToken = await cred.user.getIdToken();
        await postTokenToBackend(idToken);
        await signOut(auth);
        window.location.href = '/';
      } catch (err) {
        showMessage(loginForm, err.message || 'Login failed.');
      }
    });
  }

  const resetForm = document.querySelector('[data-firebase-auth="reset"]');
  if (resetForm) {
    resetForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const email = getFieldValue(resetForm, 'email');
      if (!email) {
        showMessage(resetForm, 'Email is required.');
        return;
      }
      try {
        await sendPasswordResetEmail(auth, email);
        showMessage(resetForm, 'Reset link sent to your email.', false);
      } catch (err) {
        showMessage(resetForm, err.message || 'Unable to send reset email.');
      }
    });
  }
};

init();
