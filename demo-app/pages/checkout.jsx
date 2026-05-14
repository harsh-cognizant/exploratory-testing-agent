import { useState } from 'react';
import { useRouter } from 'next/router';
import { useCart } from './_app';

export default function Checkout() {
  const router = useRouter();
  const { cartItems, getCartTotal, clearCart } = useCart();
  const [isProcessing, setIsProcessing] = useState(false);
  const [orderPlaced, setOrderPlaced] = useState(false);

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    address: '',
    city: '',
    state: '',
    zipCode: '',
    cardNumber: '',
    cardExpiry: '',
    cardCvv: '',
  });

  const [errors, setErrors] = useState({});

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.fullName.trim()) newErrors.fullName = 'Full name is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!formData.address.trim()) newErrors.address = 'Address is required';
    if (!formData.city.trim()) newErrors.city = 'City is required';
    if (!formData.state.trim()) newErrors.state = 'State is required';
    if (!formData.zipCode.trim()) newErrors.zipCode = 'Zip code is required';

    // BUG-004: No validation for card number format
    // Correct implementation would check:
    // - Card number should only contain digits
    // - Card number should be 13-19 digits
    // But this implementation has NO checks, accepts letters and any length

    if (!formData.cardNumber.trim()) {
      newErrors.cardNumber = 'Card number is required';
    }
    // BUG: Missing validation for card format
    // Should have: else if (!/^\d{13,19}$/.test(formData.cardNumber.replace(/\s/g, '')))
    // Should have: newErrors.cardNumber = 'Card number must be 13-19 digits';

    if (!formData.cardExpiry.trim()) {
      newErrors.cardExpiry = 'Expiry date is required';
    }

    if (!formData.cardCvv.trim()) {
      newErrors.cardCvv = 'CVV is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsProcessing(true);

    // Simulate payment processing
    setTimeout(() => {
      setOrderPlaced(true);
      clearCart();
      setIsProcessing(false);

      // Redirect to success page after 2 seconds
      setTimeout(() => {
        router.push('/products');
      }, 2000);
    }, 1500);
  };

  if (cartItems.length === 0 && !orderPlaced) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <h1>Your cart is empty</h1>
        <p style={{ color: '#666', marginTop: '16px', marginBottom: '24px' }}>
          Please add items before checking out
        </p>
        <button
          className="btn btn-primary"
          onClick={() => router.push('/products')}
        >
          Continue Shopping
        </button>
      </div>
    );
  }

  if (orderPlaced) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <div style={{ fontSize: '64px', marginBottom: '24px' }}>✓</div>
        <h1>Order Placed Successfully!</h1>
        <p style={{ color: '#666', marginTop: '16px', marginBottom: '24px' }}>
          Thank you for your purchase. Your order confirmation has been sent to {formData.email}
        </p>
        <p style={{ color: '#999', fontSize: '12px' }}>Redirecting to products...</p>
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ marginBottom: '32px' }}>Checkout</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '32px' }}>
        <form onSubmit={handleSubmit}>
          <div className="card" style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Shipping Address</h2>

            <div className="form-group">
              <label htmlFor="fullName">Full Name</label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                value={formData.fullName}
                onChange={handleInputChange}
                data-testid="fullname-input"
                placeholder="John Doe"
              />
              {errors.fullName && <div className="error-message">{errors.fullName}</div>}
            </div>

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
                data-testid="email-input"
                placeholder="john@example.com"
              />
              {errors.email && <div className="error-message">{errors.email}</div>}
            </div>

            <div className="form-group">
              <label htmlFor="address">Street Address</label>
              <input
                id="address"
                name="address"
                type="text"
                value={formData.address}
                onChange={handleInputChange}
                data-testid="address-input"
                placeholder="123 Main St"
              />
              {errors.address && <div className="error-message">{errors.address}</div>}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label htmlFor="city">City</label>
                <input
                  id="city"
                  name="city"
                  type="text"
                  value={formData.city}
                  onChange={handleInputChange}
                  data-testid="city-input"
                  placeholder="New York"
                />
                {errors.city && <div className="error-message">{errors.city}</div>}
              </div>

              <div className="form-group">
                <label htmlFor="state">State</label>
                <input
                  id="state"
                  name="state"
                  type="text"
                  value={formData.state}
                  onChange={handleInputChange}
                  data-testid="state-input"
                  placeholder="NY"
                />
                {errors.state && <div className="error-message">{errors.state}</div>}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="zipCode">Zip Code</label>
              <input
                id="zipCode"
                name="zipCode"
                type="text"
                value={formData.zipCode}
                onChange={handleInputChange}
                data-testid="zipcode-input"
                placeholder="10001"
              />
              {errors.zipCode && <div className="error-message">{errors.zipCode}</div>}
            </div>
          </div>

          <div className="card">
            <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Payment Information</h2>

            <div className="form-group">
              <label htmlFor="cardNumber">Card Number</label>
              <input
                id="cardNumber"
                name="cardNumber"
                type="text"
                value={formData.cardNumber}
                onChange={handleInputChange}
                data-testid="card-number-input"
                placeholder="1234 5678 9012 3456"
              />
              {/* BUG-004: No validation message shown even if card format is invalid */}
              {errors.cardNumber && <div className="error-message">{errors.cardNumber}</div>}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label htmlFor="cardExpiry">Expiry Date (MM/YY)</label>
                <input
                  id="cardExpiry"
                  name="cardExpiry"
                  type="text"
                  value={formData.cardExpiry}
                  onChange={handleInputChange}
                  data-testid="expiry-input"
                  placeholder="12/25"
                />
                {errors.cardExpiry && <div className="error-message">{errors.cardExpiry}</div>}
              </div>

              <div className="form-group">
                <label htmlFor="cardCvv">CVV</label>
                <input
                  id="cardCvv"
                  name="cardCvv"
                  type="text"
                  value={formData.cardCvv}
                  onChange={handleInputChange}
                  data-testid="cvv-input"
                  placeholder="123"
                />
                {errors.cardCvv && <div className="error-message">{errors.cardCvv}</div>}
              </div>
            </div>

            {/* Bug explanation */}
            <div
              style={{
                marginTop: '16px',
                padding: '12px',
                background: '#fffbea',
                border: '1px solid #ffd666',
                borderRadius: '4px',
                fontSize: '11px',
                color: '#666',
              }}
              data-testid="bug-explanation"
            >
              <strong>BUG-004 Demo:</strong> Try entering letters or unusually long numbers in the Card Number field
              (e.g., "abcdefgh" or "123456789012345678901"). The form will accept it without validation error.
              Should only accept 13-19 digits.
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            data-testid="place-order-btn"
            style={{ width: '100%', marginTop: '24px', padding: '12px' }}
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Place Order'}
          </button>
        </form>

        <div>
          <div className="card" style={{ position: 'sticky', top: '24px' }}>
            <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Order Summary</h2>

            {cartItems.map((item) => (
              <div key={item.id} style={{ marginBottom: '12px', fontSize: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>{item.emoji} {item.name}</span>
                  <span>{item.quantity}x</span>
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    color: '#666',
                    fontSize: '12px',
                  }}
                  data-testid={`order-item-${item.id}`}
                >
                  <span>${item.price.toFixed(2)} each</span>
                  <span>${(item.price * item.quantity).toFixed(2)}</span>
                </div>
              </div>
            ))}

            <div style={{ borderTop: '1px solid #eee', paddingTop: '12px', marginTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span>Subtotal:</span>
                <span data-testid="checkout-subtotal">${getCartTotal().toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span>Shipping:</span>
                <span>$9.99</span>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontWeight: 'bold',
                  fontSize: '16px',
                }}
              >
                <span>Total:</span>
                <span data-testid="checkout-total">
                  ${(getCartTotal() + 9.99).toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
