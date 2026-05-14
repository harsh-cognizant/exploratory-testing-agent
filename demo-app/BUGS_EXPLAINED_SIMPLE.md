# 🎯 DEMO APP - SIMPLIFIED EXPLANATION

## WHAT IS THIS?

A **fake e-commerce website** with 4 intentional bugs planted inside. The Exploratory Testing Agent will automatically explore this website, find the bugs, and write test cases for them.

---

## THE 4 PAGES

```
HOME (/) 
    ↓
PRODUCTS (/products)  ← BUG-002 can happen here
    ↓
ADD TO CART
    ↓
CART (/cart)          ← BUG-003 can happen here
    ↓
LOGIN (/login)        ← BUG-001 can happen here
    ↓
CHECKOUT (/checkout)  ← BUG-004 can happen here
    ↓
SUCCESS PAGE
```

---

## SIMPLE EXPLANATION OF EACH BUG

### 🔴 BUG-001: Login Accepts Empty Password

**What it is:** The login form doesn't check if password is empty

**What should happen:**
```
User enters:
  Email: test@example.com
  Password: (empty)
  
System should say: ❌ "Password is required"
```

**What actually happens:**
```
User enters:
  Email: test@example.com  
  Password: (empty)
  
System says: ✅ "Welcome, you're logged in!" (WRONG!)
```

**Why it's bad:** Anyone can log in without a password!

---

### 🔴 BUG-002: Cart Count Shows NaN

**What it is:** When you add the same product 6+ times, the cart count breaks

**What should happen:**
```
Add "Headphones" button clicked:
- 1st time → Cart shows: 1
- 2nd time → Cart shows: 2
- 3rd time → Cart shows: 3
- 4th time → Cart shows: 4
- 5th time → Cart shows: 5
- 6th time → Cart shows: 6  ✅
- 7th time → Cart shows: 7  ✅
```

**What actually happens:**
```
Add "Headphones" button clicked:
- 1st time → Cart shows: 1
- 2nd time → Cart shows: 2
- 3rd time → Cart shows: 3
- 4th time → Cart shows: 4
- 5th time → Cart shows: 5
- 6th time → Cart shows: NaN  ❌ (BROKEN!)
- 7th time → Cart shows: NaN  ❌ (STILL BROKEN!)
```

**Why it's bad:** Users can't tell how many items are in their cart!

---

### 🔴 BUG-003: Negative Quantities Accepted

**What it is:** The cart accepts negative numbers for quantity

**What should happen:**
```
User tries to enter: -5 in Quantity field
System says: ❌ "Quantity must be positive"
```

**What actually happens:**
```
User enters: -5 in Quantity field
System accepts it: ✅ "OK, -5 items for $-79.95"
Subtotal: -$79.95  ❌ (WRONG!)
```

**Why it's bad:** Customer gets money BACK instead of paying!

---

### 🔴 BUG-004: Card Number Not Validated

**What it is:** The checkout form accepts any card number, even invalid ones

**What should happen:**
```
Valid card: 4532 1234 5678 9010 ✅
Invalid input: "abcdefgh"  ❌ System rejects: "Must be 13-19 digits"
Invalid input: "12345"     ❌ System rejects: "Too short"
Invalid input: "123456789012345678901" ❌ System rejects: "Too long"
```

**What actually happens:**
```
Valid card: 4532 1234 5678 9010 ✅
Invalid input: "abcdefgh"  ✅ System accepts it (WRONG!)
Invalid input: "12345"     ✅ System accepts it (WRONG!)
Invalid input: "123456789012345678901" ✅ System accepts it (WRONG!)
```

**Why it's bad:** System could accept fake payment cards!

---

## HOW TO RUN THE DEMO APP

### STEP 1: Install Node.js
Download from: https://nodejs.org (get LTS version)

### STEP 2: Open Terminal/Command Prompt
Navigate to the `demo-app` folder

### STEP 3: Run These Commands

```bash
# Install all packages needed
npm install

# Start the website
npm run dev
```

### STEP 4: Open Your Browser
Go to: `http://localhost:3001`

You should see the DemoShop homepage with 6 products.

---

## HOW TO MANUALLY FIND EACH BUG (For Testing)

### Finding BUG-001:
1. Click "Login" in menu
2. Type email: `test@test.com`
3. Leave password **blank**
4. Click "Login" button
5. You should get an error BUT YOU DON'T! ❌

### Finding BUG-002:
1. Click "Add to Cart" on Headphones button **6 times**
2. Look at the cart count badge (top right)
3. It should show "6" but it shows "NaN" ❌

### Finding BUG-003:
1. Add 1 item to cart
2. Go to Cart page
3. Find the quantity field
4. Change it from "1" to "-5"
5. The subtotal should become negative! ❌

### Finding BUG-004:
1. Add item to cart
2. Go to Checkout
3. Try to place order but enter in Card Number: `abcdefgh` (letters!)
4. It accepts it! Should reject it ❌

---

## WHAT THE AGENT WILL DO

The AI agent will:

1. **Explore the website** like a user would
2. **Behave like 3 different people:**
   - Confused person: enters wrong data, leaves fields empty
   - Expert user: clicks fast, adds items repeatedly
   - Malicious person: tries to break things intentionally
3. **Find the 4 bugs** automatically
4. **Take screenshots** of each bug
5. **Write test code** that proves the bug exists
6. **Create a report** showing:
   - What was covered (in %)
   - What bugs were found
   - Test cases to fix them

---

## FILE STRUCTURE (Simple Version)

```
demo-app/
├── pages/
│   ├── login.jsx       ← BUG-001 is here
│   ├── products.jsx    ← BUG-002 is here  
│   ├── cart.jsx        ← BUG-003 is here
│   └── checkout.jsx    ← BUG-004 is here
├── styles/
│   └── globals.css     ← Colors, fonts, styling
├── package.json        ← List of software needed
└── README.md          ← Full instructions
```

---

## QUICK CHECKLIST

- [ ] Node.js installed
- [ ] Terminal opened in demo-app folder
- [ ] Ran `npm install`
- [ ] Ran `npm run dev`
- [ ] Opened http://localhost:3001
- [ ] Can see products page
- [ ] All 4 bugs confirmed working
- [ ] Ready for agent testing

---

## SUMMARY

| Bug | Page | Problem | Severity |
|-----|------|---------|----------|
| 001 | Login | Empty password accepted | 🔴 HIGH |
| 002 | Products | Cart count = NaN | 🟠 MEDIUM |
| 003 | Cart | Negative qty accepted | 🔴 HIGH |
| 004 | Checkout | Invalid card accepted | 🔴 HIGH |

---

## NEED HELP?

If something doesn't work:

1. **"npm install" fails:** Make sure Node.js is installed correctly
2. **"Port 3001 in use":** Change port number or kill the process
3. **"Bugs not showing":** Clear browser cache and refresh
4. **"Page won't load":** Check terminal for error messages

That's it! You now have a complete demo e-commerce website with 4 deliberate bugs ready for the agent to find. 🎉
