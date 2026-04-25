import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyD5NIzFpDXk5SB-H7setET80iqUikiC7m8",
  authDomain: "sqllab-498d7.firebaseapp.com",
  projectId: "sqllab-498d7",
  storageBucket: "sqllab-498d7.firebasestorage.app",
  messagingSenderId: "577963944164",
  appId: "1:577963944164:web:d09278b597ce6dc28fa4f1"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export default app;