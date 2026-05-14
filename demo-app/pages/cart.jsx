import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useCart } from './_app';

export default function Cart() {
  const router = useRouter();
  const { cartItems, updateQuantity, removeFromCart, getCartTotal } = useCart();
  const [errors, setErrors] = useState({});

  const handleQuantityChange = (productId, value) => {
    // BUG-003: No validation to prevent negative quantities
    // Correct implementation should validate: if (value < 0) return;
    // But this code allows negative numbers to be entered
    
    try {
      const quantity = parseInt(value) || 0;
      // BUG: Missing validation here
      // Should check: if (quantity < 0) { showError; return; }
      // Instead, it directly accepts negative values
      updateQuantity(productId, quantity);
    } catch (e) {
      setErrors({ ...errors, [productId]: 'Invalid quantity' });
    }
  };

  if (cartItems.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <h1>Your Cart is Empty</h1>
        <p style={{ color: '#666', marginTop: '16px', marginBottom: '24px' }}>
          Add some items from our products page
        </p>
        <Link href="/products">
          <button className="btn btn-primary">Continue Shopping</button>
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ marginBottom: '32px' }}>Shopping Cart</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '32px' }}>
        <div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #eee' }}>
                <th style={{ textAlign: 'left', padding: '12px', fontWeight: '600' }}>Product</th>
                <th style={{ textAlign: 'center', padding: '12px', fontWeight: '600' }}>Price</th>
                <th style={{ textAlign: 'center', padding: '12px', fontWeight: '600' }}>Quantity</th>
                <th style={{ textAlign: 'right', padding: '12px', fontWeight: '600' }}>Total</th>
                <th style={{ textAlign: 'center', padding: '12px', fontWeight: '600' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {cartItems.map((item) => (
                <tr key={item.id} style={{ borderBottom: '1px solid #eee' }} data-testid={`cart-item-${item.id}`}>
                  <td style={{ padding: '12px' }}>
                    <div style={{ fontSize: '20px', marginRight: '8px', display: 'inline' }}>
                      {item.emoji}
                    </div>
                    {item.name}
                  </td>
                  <td style={{ textAlign: 'center', padding: '12px' }} data-testid={`item-price-${item.id}`}>
                    ${item.price.toFixed(2)}
                  </td>
                  <td style={{ textAlign: 'center', padding: '12px' }}>
                    <input
                      type="number"
                      value={item.quantity}
                      onChange={(e) => handleQuantityChange(item.id, e.target.value)}
                      data-testid={`quantity-input-${item.id}`}
                      style={{
                        width: '60px',
                        padding: '6px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        textAlign: 'center',
                      }}
                    />
                    {/* BUG-003: No validation error shown for negative quantities */}
                    {errors[item.id] && (
                      <div className="error-message">{errors[item.id]}</div>
                    )}
                  </td>
                  <td
                    style={{ textAlign: 'right', padding: '12px', fontWeight: '600' }}
                    data-testid={`item-total-${item.id}`}
                  >
                    ${(item.price * item.quantity).toFixed(2)}
                  </td>
                  <td style={{ textAlign: 'center', padding: '12px' }}>
                    <button
                      className="btn btn-danger"
                      onClick={() => removeFromCart(item.id)}
                      data-testid={`remove-btn-${item.id}`}
                      style={{ padding: '6px 12px', fontSize: '12px' }}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Bug explanation */}
          <div
            style={{
              marginTop: '24px',
              padding: '16px',
              background: '#fffbea',
              border: '1px solid #ffd666',
              borderRadius: '4px',
              fontSize: '12px',
              color: '#666',
            }}
            data-testid="bug-explanation"
          >
            <strong>BUG-003 Demo:</strong> Try entering a negative number (e.g., -5) in the Quantity field.
            The system will accept it without showing any validation error, and the subtotal will calculate
            a negative amount. Correct behavior: should reject negative quantities.
          </div>
        </div>

        <div>
          <div className="card">
            <h2 style={{ marginBottom: '16px', fontSize: '18px' }}>Order Summary</h2>

            <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between' }}>
              <span>Subtotal:</span>
              <span data-testid="subtotal">${getCartTotal().toFixed(2)}</span>
            </div>

            <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between' }}>
              <span>Shipping:</span>
              <span>$9.99</span>
            </div>

            <div style={{ marginBottom: '24px', paddingBottom: '12px', borderBottom: '1px solid #eee' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', fontSize: '16px' }}>
                <span>Total:</span>
                <span data-testid="total-price">
                  ${(getCartTotal() + 9.99).toFixed(2)}
                </span>
              </div>
            </div>

            <button
              className="btn btn-primary"
              onClick={() => router.push('/checkout')}
              data-testid="proceed-to-checkout-btn"
              style={{ width: '100%', marginBottom: '12px' }}
            >
              Proceed to Checkout
            </button>

            <Link href="/products">
              <button className="btn btn-secondary" style={{ width: '100%' }}>
                Continue Shopping
              </button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
