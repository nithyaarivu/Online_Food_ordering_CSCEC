import streamlit as st
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Kitchen Ordering System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        padding: 0.5rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1e40af;
    }
    .price-tag {
        color: #2563eb;
        font-size: 1.25rem;
        font-weight: bold;
    }
    .success-box {
        background-color: #dcfce7;
        padding: 1.5rem;
        border-radius: 8px;
        border: 2px solid #16a34a;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'order_history' not in st.session_state:
    st.session_state.order_history = []
if 'inventory' not in st.session_state:
    st.session_state.inventory = None
if 'show_success' not in st.session_state:
    st.session_state.show_success = False


# Function to load Excel file directly
@st.cache_data
def load_excel_data(file_path):
    """Load and parse the Excel file with 4 sheets"""
    all_items = []
    item_id = 1

    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel('C://Users//TITANS//Desktop//Food_items', sheet_name=sheet_name, header=None)

            # Start from row 2 (index 2)
            for idx in range(2, len(df)):
                row = df.iloc[idx]

                # Each row has 3 sets of items (columns 0-2, 4-6, 8-10)
                item_sets = [
                    {'name': 0, 'spec': 1, 'price': 2},
                    {'name': 4, 'spec': 5, 'price': 6},
                    {'name': 8, 'spec': 9, 'price': 10}
                ]

                for item_set in item_sets:
                    try:
                        name = row[item_set['name']]
                        spec = row[item_set['spec']]
                        price_str = row[item_set['price']]

                        # Skip empty rows
                        if pd.isna(name) or str(name).strip() == '':
                            continue

                        # Extract price
                        import re
                        price_match = re.search(r'[\d.]+', str(price_str))
                        price = float(price_match.group()) if price_match else 0

                        all_items.append({
                            'id': item_id,
                            'name': str(name).strip(),
                            'category': sheet_name,
                            'unit': str(spec).strip() if not pd.isna(spec) else '',
                            'price': price
                        })
                        item_id += 1
                    except:
                        continue

        return pd.DataFrame(all_items)
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        st.error(f"Please make sure the file exists at: {file_path}")
        return None


# Function to add item to cart
def add_to_cart(item_id, item_name, price, unit, category):
    if item_id in st.session_state.cart:
        st.session_state.cart[item_id]['quantity'] += 1
    else:
        st.session_state.cart[item_id] = {
            'name': item_name,
            'price': price,
            'unit': unit,
            'category': category,
            'quantity': 1
        }


# Function to update quantity
def update_quantity(item_id, change):
    if item_id in st.session_state.cart:
        st.session_state.cart[item_id]['quantity'] += change
        if st.session_state.cart[item_id]['quantity'] <= 0:
            del st.session_state.cart[item_id]


# Function to calculate cart total
def calculate_total():
    total = 0
    for item in st.session_state.cart.values():
        total += item['price'] * item['quantity']
    return total


# Function to complete order
def complete_order():
    if st.session_state.cart:
        order = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'items': dict(st.session_state.cart),
            'total': calculate_total()
        }
        st.session_state.order_history.append(order)
        st.session_state.cart = {}
        st.session_state.show_success = True
        return True
    return False


# ==========================================
# IMPORTANT: CHANGE THIS PATH TO YOUR FILE
# ==========================================
EXCEL_FILE_PATH = "JVC 规格品类.xls"  # Put your file in the same folder as this script
# Or use full path like: "C:/Users/TITANS/Desktop/JVC 规格品类.xls"

# Load inventory on first run
if st.session_state.inventory is None:
    with st.spinner("Loading inventory..."):
        st.session_state.inventory = load_excel_data(EXCEL_FILE_PATH)

    if st.session_state.inventory is None:
        st.error("❌ Could not load inventory file!")
        st.info(f"📁 Looking for file at: {EXCEL_FILE_PATH}")
        st.info("💡 Please update EXCEL_FILE_PATH in the code with the correct path to your Excel file")
        st.stop()

# Main App
inventory = st.session_state.inventory

# Header
st.title("🍽️ Kitchen Ordering System")
st.markdown(f"**JVC Staff Kitchen Materials** • {len(inventory)} items available")

# Show success message after order
if st.session_state.show_success:
    st.markdown("""
    <div class='success-box'>
        <h2>✅ Order Placed Successfully!</h2>
        <p>Your order has been recorded. You can place a new order below.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Continue Shopping"):
        st.session_state.show_success = False
        st.rerun()
    st.divider()

# Navigation
page = st.radio(
    "Navigation",
    ["🏠 Browse Items", "🛒 Cart", "📜 Order History"],
    horizontal=True,
    label_visibility="collapsed"
)

# Page 1: Browse Items
if page == "🏠 Browse Items":
    st.subheader("Browse Items")

    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("🔍 Search items", "", key="search")
    with col2:
        categories = ['All'] + sorted(inventory['category'].unique().tolist())
        selected_category = st.selectbox("Category", categories)

    # Filter inventory
    filtered_df = inventory.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(search_query, case=False, na=False)
        ]
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]

    st.markdown(f"**{len(filtered_df)} items found**")

    # Display items
    for idx, row in filtered_df.iterrows():
        col1, col2, col3 = st.columns([4, 2, 2])

        with col1:
            st.markdown(f"**{row['name']}**")
            st.caption(f"{row['category']} • {row['unit']}")

        with col2:
            st.markdown(f"<span class='price-tag'>{row['price']:.2f} AED</span>", unsafe_allow_html=True)

        with col3:
            if row['id'] in st.session_state.cart:
                qty = st.session_state.cart[row['id']]['quantity']
                st.success(f"In cart: {qty}")

            if st.button("➕ Add", key=f"add_{row['id']}"):
                add_to_cart(row['id'], row['name'], row['price'], row['unit'], row['category'])
                st.rerun()

        st.divider()

    # Cart summary at bottom
    if st.session_state.cart:
        cart_count = sum(item['quantity'] for item in st.session_state.cart.values())
        st.info(f"🛒 Cart: {cart_count} items • Total: {calculate_total():.2f} AED")

# Page 2: Cart
elif page == "🛒 Cart":
    st.subheader("Your Order")

    if not st.session_state.cart:
        st.info("🛒 Your cart is empty. Add items from the Browse page!")
    else:
        # Display cart items
        for item_id, item in st.session_state.cart.items():
            col1, col2, col3, col4 = st.columns([4, 2, 2, 1])

            with col1:
                st.markdown(f"**{item['name']}**")
                st.caption(f"{item['category']} • {item['unit']}")

            with col2:
                st.markdown(f"{item['price']:.2f} AED")

            with col3:
                subcol1, subcol2, subcol3 = st.columns(3)
                with subcol1:
                    if st.button("➖", key=f"dec_{item_id}"):
                        update_quantity(item_id, -1)
                        st.rerun()
                with subcol2:
                    st.markdown(f"**{item['quantity']}**")
                with subcol3:
                    if st.button("➕", key=f"inc_{item_id}"):
                        update_quantity(item_id, 1)
                        st.rerun()

            with col4:
                if st.button("🗑️", key=f"del_{item_id}"):
                    del st.session_state.cart[item_id]
                    st.rerun()

            st.markdown(f"**Subtotal: {item['price'] * item['quantity']:.2f} AED**")
            st.divider()

        # Order summary
        st.markdown("### 📊 Order Summary")
        total_items = sum(item['quantity'] for item in st.session_state.cart.values())
        total_price = calculate_total()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Items", total_items)
        with col2:
            st.metric("Total Amount", f"{total_price:.2f} AED")

        st.divider()

        # Complete order button
        if st.button("✅ Complete Order", type="primary", use_container_width=True):
            if complete_order():
                st.rerun()

# Page 3: Order History
elif page == "📜 Order History":
    st.subheader("Order History")

    if not st.session_state.order_history:
        st.info("📜 No orders yet. Place your first order!")
    else:
        st.success(f"**Total Orders: {len(st.session_state.order_history)}**")

        for idx, order in enumerate(reversed(st.session_state.order_history)):
            order_num = len(st.session_state.order_history) - idx

            with st.expander(f"📦 Order #{order_num} • {order['date']} • {order['total']:.2f} AED", expanded=(idx == 0)):
                # Display items in a table format
                items_data = []
                for item in order['items'].values():
                    items_data.append({
                        'Item': item['name'],
                        'Category': item['category'],
                        'Unit Price': f"{item['price']:.2f} AED",
                        'Quantity': item['quantity'],
                        'Total': f"{item['price'] * item['quantity']:.2f} AED"
                    })

                df_order = pd.DataFrame(items_data)
                st.dataframe(df_order, use_container_width=True, hide_index=True)

                st.markdown(f"### 💰 Order Total: {order['total']:.2f} AED")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"📦 Items: {len(inventory)}")
with col2:
    cart_items = sum(item['quantity'] for item in st.session_state.cart.values())
    st.caption(f"🛒 In Cart: {cart_items}")
with col3:
    st.caption(f"📜 Orders: {len(st.session_state.order_history)}")