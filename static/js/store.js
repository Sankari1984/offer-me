const BASE_URL = "https://offer-me.onrender.com";

document.addEventListener('DOMContentLoaded', async function () {
  const urlParams = new URLSearchParams(window.location.search);
  let userId = urlParams.get('user_id') || localStorage.getItem('user_id');
  const highlightId = urlParams.get('highlight');
  const isVisitor = urlParams.get('user_id') !== null;
  if (isVisitor) {
    const storeActions = document.querySelector('.store-actions');
    const bottomNav = document.querySelector('.bottom-nav');
    if (storeActions) storeActions.style.display = 'none';
    if (bottomNav) bottomNav.style.display = 'none';
  }

  if (!userId) {
    window.location.href = 'login.html';
    return;
  }

  const productsContainer = document.getElementById('productsContainer');

  fetch(`${BASE_URL}/products`)
    .then(response => response.json())
    .then(products => {
      let userProducts = products.filter(p => p.user_id === userId);

      if (highlightId) {
        const highlighted = userProducts.find(p => p.id === highlightId);
        if (highlighted) {
          userProducts = [highlighted, ...userProducts.filter(p => p.id !== highlightId)];
        }
      }

      if (userProducts.length === 0) {
        productsContainer.innerHTML = "<p style='text-align:center;'>لا يوجد منتجات مضافة حالياً.</p>";
      } else {
        productsContainer.innerHTML = '';
        userProducts.forEach(product => {
          const productCard = document.createElement('div');
          productCard.classList.add('product-card');

          const fullUrl = `${BASE_URL}${product.image}`;
          let mediaElement = '';
          if (fullUrl.endsWith('.mp4') || fullUrl.endsWith('.webm') || fullUrl.endsWith('.mov')) {
            mediaElement = `
              <video controls style="width: 100%; height: 180px; background-color: #000; border-radius: 6px;">
                <source src="${fullUrl}" type="video/mp4">
                المتصفح لا يدعم تشغيل الفيديو.
              </video>`;
          } else {
            mediaElement = `<img src="${fullUrl}" alt="${product.name}" onclick="openPopup('${fullUrl}')" style="height: 180px;">`;
          }

          productCard.innerHTML = `
            ${mediaElement}
            <div class="product-card-content">
              <h3>${product.name}</h3>
              ${product.price ? `<p style="color:#25a18e; font-weight:bold;">💰 السعر: ${product.price} ريال</p>` : ''}
              ${product.post ? `<p class="product-ai-post">${product.post}</p>` : ""}
              <div class="share-buttons">
                <button onclick="copyPost('${product.post || ''}')">📝 نسخ</button>
                <button onclick="shareFacebook('${product.post || ''}')">🌐 فيسبوك</button>
                <button onclick="shareInstagram('${product.post || ''}')">📸 انستغرام</button>
                <button onclick="deleteProduct('${product.id}')">🗑️ حذف</button>
                <button onclick="likeProduct('${product.id}')">👍 إعجاب</button>
                <span id="like-count-${product.id}">0</span>
              </div>
            </div>
          `;

          productsContainer.appendChild(productCard);

          // تحميل عدد اللايكات من السيرفر
          fetch(`${BASE_URL}/likes/${product.id}`)
            .then(res => res.json())
            .then(data => {
              document.getElementById(`like-count-${product.id}`).innerText = data.likes;
            });
        });
      }
    })
    .catch(error => {
      console.error('خطأ في تحميل المنتجات:', error);
      productsContainer.innerHTML = "<p>❌ حدث خطأ أثناء تحميل المنتجات.</p>";
    });

  importFirebaseMessaging(userId);
});

function copyPost(text) {
  const tempInput = document.createElement('textarea');
  tempInput.value = text;
  document.body.appendChild(tempInput);
  tempInput.select();
  document.execCommand('copy');
  document.body.removeChild(tempInput);
  alert("✅ تم نسخ البوست!");
}

function shareFacebook(text) {
  const url = `https://www.facebook.com/sharer/sharer.php?u=&quote=${encodeURIComponent(text)}`;
  window.open(url, '_blank');
}

function shareInstagram(text) {
  navigator.clipboard.writeText(text).then(() => {
    alert("✅ تم نسخ البوست! الصقه في انستغرام يدوياً.");
  });
}

function deleteProduct(productId) {
  if (!confirm("❗ هل أنت متأكد أنك تريد حذف هذا المنتج؟")) return;
  fetch(`${BASE_URL}/delete-product/${productId}`, {
    method: 'DELETE'
  })
    .then(res => res.json())
    .then(data => {
      alert(data.message);
      location.reload();
    })
    .catch(err => {
      alert("❌ حدث خطأ في حذف المنتج");
      console.error(err);
    });
}

function likeProduct(productId) {
  fetch(`${BASE_URL}/like/${productId}`, {
    method: 'POST'
  })
    .then(response => response.json())
    .then(data => {
      document.getElementById(`like-count-${productId}`).innerText = data.likes;
    })
    .catch(error => console.error("خطأ في تسجيل الإعجاب:", error));
}

function goToUpload() {
  window.location.href = 'upload.html';
}

function goToManageTabs() {
  window.location.href = 'manage_tabs.html';
}

function openPopup(imageSrc) {
  const popup = document.createElement('div');
  popup.style.position = 'fixed';
  popup.style.top = '0';
  popup.style.left = '0';
  popup.style.width = '100%';
  popup.style.height = '100%';
  popup.style.background = 'rgba(0,0,0,0.7)';
  popup.style.display = 'flex';
  popup.style.justifyContent = 'center';
  popup.style.alignItems = 'center';
  popup.style.zIndex = '10000';
  popup.innerHTML = `<img src="${imageSrc}" style="max-width: 90%; max-height: 90%; border-radius: 10px;">`;
  popup.onclick = () => popup.remove();
  document.body.appendChild(popup);
}

async function importFirebaseMessaging(userId) {
  const { initializeApp } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
  const { getMessaging, getToken, onMessage } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging.js");

  const firebaseConfig = {
    apiKey: "AIzaSyDnmeJiICl_j7UJ0d1xfKsA7KmizVe_QxA",
    authDomain: "offer-me-c0c4b.firebaseapp.com",
    projectId: "offer-me-c0c4b",
    storageBucket: "offer-me-c0c4b.firebasestorage.app",
    messagingSenderId: "413164622012",
    appId: "1:413164622012:web:91cd8b7c24e9a0353100b9",
    measurementId: "G-N37ZR1W8GD"
  };

  const app = initializeApp(firebaseConfig);
  const messaging = getMessaging(app);

  Notification.requestPermission().then(permission => {
    if (permission === 'granted') {
      getToken(messaging, {
        vapidKey: 'BHsTG0e2m4UdrvrUuVKuHGwpbVya0g4F5NtF1EE8vnykR889YDHVLRu2z0t9gohDEkCj4UeDrfEUW7RBFpi4Nb8'
      }).then(currentToken => {
        if (currentToken) {
          console.log('🔑 Token:', currentToken);
          fetch(`${BASE_URL}/save-token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: userId,
              token: currentToken
            })
          });
        } else {
          console.warn('⚠️ لم يتم الحصول على التوكن');
        }
      });
    }
  });

  onMessage(messaging, (payload) => {
    console.log('📩 إشعار داخل الموقع:', payload);
    alert(payload.notification.title + "\n" + payload.notification.body);
  });
}
