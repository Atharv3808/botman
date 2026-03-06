import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyDNL2wpbb-V1XVKAVf8Pv32TiOEYqlV5Po",
  authDomain: "botman-c802c.firebaseapp.com",
  projectId: "botman-c802c",
  storageBucket: "botman-c802c.appspot.com",
  messagingSenderId: "52258015757",
  appId: "1:52258015757:web:cfcf4abfbd1c9c7684e344",
  measurementId: "G-17WZTKPLSS"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
