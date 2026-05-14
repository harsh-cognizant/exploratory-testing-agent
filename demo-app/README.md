# 🛍️ DemoShop - E-Commerce Testing Demo App

A minimal Next.js e-commerce application with **4 pre-planted bugs** designed for testing the Exploratory Testing & Coverage Gap Discovery Agent.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ (LTS recommended)
- npm or yarn

### Setup Instructions

```bash
# 1. Navigate to demo-app directory (if not already there)
cd demo-app

# 2. Install dependencies
npm install

# 3. Start the development server
npm run dev

# The app will be available at: http://localhost:3001
```

### Verify It's Working

1. Open your browser and go to `http://localhost:3001`
2. You should see the DemoShop homepage with products
3. Try adding items to cart - the cart count should update
4. Navigate through: Products → Cart → Login → Checkout

---

## 🐛 Pre-Planted Bugs Reference Guide

The agent should discover these bugs autonomously through behavioral exploration:

### BUG-001: Login Form Accepts Empty Password ⚠️ HIGH SEVERITY

**Location:** `/login` page  
**Type:** Missing Input Validation  
**How to trigger manually:**
1. Go to http://localhost:3001/login
2. Enter any email (e.g., `test@example.com`)
3. Leave password field **empty**
4. Click "Login" button
5. **Expected:** Error message saying "Password is required"
6. **Actual:** Form submits successfully without validation error

**Code location:** `pages/login.jsx` - no validation for empty password

**How agent finds it:** Confused User persona fills form with missing required field

---

### BUG-002: Cart Count Shows NaN ⚠️ MEDIUM SEVERITY

**Location:** `/products` page (header cart badge)  
**Type:** Arithmetic/Logic Error  
**How to trigger manually:**
1. Go to http://localhost:3001/products
2. Click "Add to Cart" on any product (e.g., "Wireless Headphones") **6 or more times**
3. Look at the cart count badge in the header (top right)
4. **Expected:** Should show "6" (or higher)
5. **Actual:** May display as `NaN` after 6+ additions

**Code location:** `pages/_app.jsx` - `getCartCount()` function multiplies by string when quantity > 5

**How agent finds it:** Power User adds same item repeatedly to test edge cases

---

### BUG-003: Negative Quantities Accepted ⚠️ HIGH SEVERITY

**Location:** `/cart` page (quantity field)  
**Type:** Missing Input Validation  
**How to trigger manually:**
1. Add at least one item to cart and go to http://localhost:3001/cart
2. In the "Quantity" column for any item, clear the field and enter `-5` (negative number)
3. Press Enter or Tab to update
4. **Expected:** Error message saying "Quantity cannot be negative"
5. **Actual:** Negative quantity is accepted, and total becomes negative

**Code location:** `pages/cart.jsx` - `handleQuantityChange()` has no negative check

**How agent finds it:** Confused/Malicious User tries invalid input values

---

### BUG-004: Card Number Format Not Validated ⚠️ HIGH SEVERITY

**Location:** `/checkout` page (payment form)  
**Type:** Missing Format Validation  
**How to trigger manually:**
1. Add items to cart and proceed to checkout: http://localhost:3001/checkout
2. Fill in all fields normally EXCEPT card number
3. For "Card Number", enter invalid input:
   - Try letters: `abcdefgh`
   - Try too many digits: `12345678901234567890123`
   - Try too few digits: `123`
4. Click "Place Order"
5. **Expected:** Error message saying "Card number must be 13-19 digits"
6. **Actual:** Form accepts any input without validation

**Code location:** `pages/checkout.jsx` - `validateForm()` has no card format check

**How agent finds it:** Malicious User enters invalid payment data, confused user enters wrong data format

---

## 📊 App Structure

```
demo-app/
├── pages/
│   ├── _app.jsx           # Global wrapper + Cart Context
│   ├── _document.jsx      # HTML structure
│   ├── index.jsx          # Home → redirects to products
│   ├── login.jsx          # BUG-001: empty password validation
│   ├── products.jsx       # BUG-002: cart count NaN
│   ├── cart.jsx           # BUG-003: negative quantity
│   └── checkout.jsx       # BUG-004: card number format
├── styles/
│   └── globals.css        # Global styles + Tailwind
├── package.json
├── next.config.js
├── tailwind.config.js
├── postcss.config.js
└── README.md              # This file
```

---

## 🎯 User Flows to Test

### Happy Path (No Bugs)
1. **Products** → Browse products
2. **Add to Cart** → Add 1-2 items
3. **View Cart** → Review items (quantities 1-5)
4. **Checkout** → Fill all fields correctly
5. **Order Complete** → Success message

### Bug Discovery Paths

**For Agent Testing:**
- **Confused User:** Skip login, navigate backward, enter empty/wrong field types
- **Power User:** Add same item 6+ times, use keyboard, rapid clicks
- **Malicious User:** Enter SQL injection strings, XSS payloads, wrong data types in all fields

---

## 🔧 Development Notes

### Technologies Used
- **Framework:** Next.js 14
- **Styling:** Tailwind CSS
- **State Management:** React Context (Cart)
- **Storage:** Browser localStorage (persists cart & login)

### Key Features
- ✅ Real shopping cart with persistent storage
- ✅ Product grid with emoji product icons
- ✅ Form validation (partial - bugs intentional)
- ✅ Login state tracking
- ✅ Order summary calculations
- ✅ Responsive design

### File Size
- **Bundle Size:** ~50KB (Next.js)
- **Load Time:** < 2s on average connection

---

## 📝 Testing Checklist for Agent

The agent should:
- [ ] Discover 4 pre-planted bugs
- [ ] Generate valid Pytest test cases for each bug
- [ ] Create reproduction steps for each finding
- [ ] Capture screenshots of bugs
- [ ] Map complete app coverage (5-6 main flows)
- [ ] Identify high-risk areas (payment, auth)
- [ ] Suggest improved validation logic

---

## 🐛 Expected Test Coverage

**Total Pages:** 4  
**Total Forms:** 3 (Login, Cart updates, Checkout)  
**Total Buttons:** 10+  
**Bug Difficulty:**
- 🟢 Easy to find: BUG-001, BUG-003 (simple validation)
- 🟡 Medium: BUG-004 (format validation)
- 🔴 Tricky: BUG-002 (edge case in arithmetic)

---

## 🚀 Integration with Agent

### API Endpoints the Agent Will Call
- `GET /` - Home page → redirects to products
- `GET /login` - Login form
- `GET /products` - Product listing
- `POST /` (submit login) - Simulated in frontend
- `GET /cart` - Shopping cart
- `POST /` (cart update) - Simulated in frontend
- `GET /checkout` - Checkout form
- `POST /` (place order) - Simulated in frontend

### Expected Agent Behavior
1. **Route Discovery:** Crawler finds `/login`, `/products`, `/cart`, `/checkout`
2. **Graph Building:** Creates nodes for each page + form elements
3. **Risk Scoring:** Auth flow (login) marked as critical, payment marked as high
4. **Exploration:** Personas test each page with varied inputs
5. **Finding Capture:** Screenshots + reproduction steps for each bug
6. **Test Generation:** Pytest functions written to validate fixes

---

## 🛠️ Troubleshooting

### Port 3001 Already in Use
```bash
# Kill the process using port 3001
lsof -ti:3001 | xargs kill -9

# Or run on different port
npm run dev -- -p 3002
```

### Bugs Not Appearing
- Clear browser localStorage: Open DevTools → Application → Clear All
- Refresh page: Ctrl+Shift+R (hard refresh)
- Delete `.next` folder and rebuild: `rm -rf .next && npm run dev`

### Cart Data Not Persisting
- Make sure localStorage is enabled in browser
- Check browser console for JavaScript errors
- Try incognito/private window

---

## 📧 Contact & Questions

For questions about specific bugs or agent testing:
1. Check the bug descriptions above
2. Review code comments in each page (marked with `// BUG-XXX`)
3. Test manually first to understand expected vs actual behavior

---

## 📄 License

This demo app is part of the Exploratory Testing Agent hackathon project.

**Happy testing! 🧪**
