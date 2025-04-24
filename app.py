import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import init_db, get_session, Product, Supplier, Order, OrderItem
from datetime import datetime, timedelta

# Initialize the database
init_db()

def main():
    st.title("Inventory Management System")
    
    # Sidebar menu
    menu = st.sidebar.selectbox(
        "Menu",
        ["Dashboard", "Products", "Suppliers", "Orders"]
    )
    
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Products":
        show_products()
    elif menu == "Suppliers":
        show_suppliers()
    elif menu == "Orders":
        show_orders()

def show_dashboard():
    st.header("Dashboard")
    
    # Get statistics
    session = get_session()
    total_products = session.query(Product).count()
    total_suppliers = session.query(Supplier).count()
    total_orders = session.query(Order).count()
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Products", total_products)
    with col2:
        st.metric("Total Suppliers", total_suppliers)
    with col3:
        st.metric("Total Orders", total_orders)
    
    # Product Stock Levels Chart
    st.subheader("Product Stock Levels")
    products = session.query(Product).all()
    if products:
        df_stock = pd.DataFrame([{
            "Product": product.name,
            "Quantity": product.quantity,
        } for product in products])
        
        fig_stock = px.bar(
            df_stock,
            x="Product",
            y="Quantity",
            title="Current Stock Levels",
            color="Quantity",
            color_continuous_scale="Viridis"
        )
        fig_stock.update_layout(
            xaxis_tickangle=-45,
            height=500,  # Make the graph taller
            margin=dict(t=30, b=80)  # Adjust margins for better label visibility
        )
        st.plotly_chart(fig_stock, use_container_width=True)
    else:
        st.info("No products in inventory")
    
    # Low stock alerts
    st.subheader("Low Stock Alerts")
    low_stock = session.query(Product).filter(Product.quantity < 10).all()
    if low_stock:
        df = pd.DataFrame([{
            "Product": product.name,
            "Current Quantity": product.quantity,
            "Supplier": product.supplier.name if product.supplier else "N/A"
        } for product in low_stock])
        st.dataframe(df)
    else:
        st.info("No products are running low on stock.")

def show_products():
    st.header("Products Management")
    
    tab1, tab2 = st.tabs(["Product List", "Add Product"])
    
    session = get_session()
    
    with tab1:
        products = session.query(Product).all()
        if products:
            df = pd.DataFrame([{
                "ID": p.id,
                "Name": p.name,
                "Description": p.description,
                "Quantity": p.quantity,
                "Price": p.price,
                "Supplier": p.supplier.name if p.supplier else "N/A"
            } for p in products])
            st.dataframe(df)
            
            # Update quantity
            st.subheader("Update Stock")
            product_id = st.number_input("Product ID", min_value=1)
            new_quantity = st.number_input("New Quantity", min_value=0)
            if st.button("Update Stock"):
                product = session.query(Product).filter_by(id=product_id).first()
                if product:
                    product.quantity = new_quantity
                    session.commit()
                    st.success("Stock updated successfully!")
                else:
                    st.error("Product not found!")
    
    with tab2:
        name = st.text_input("Product Name")
        description = st.text_area("Description")
        quantity = st.number_input("Quantity", min_value=0)
        price = st.number_input("Price", min_value=0.0)
        suppliers = session.query(Supplier).all()
        supplier_names = [s.name for s in suppliers]
        supplier_name = st.selectbox("Supplier", [""] + supplier_names)
        
        if st.button("Add Product"):
            if name and price:
                supplier = session.query(Supplier).filter_by(name=supplier_name).first() if supplier_name else None
                new_product = Product(
                    name=name,
                    description=description,
                    quantity=quantity,
                    price=price,
                    supplier_id=supplier.id if supplier else None
                )
                session.add(new_product)
                session.commit()
                st.success("Product added successfully!")
            else:
                st.error("Please fill in all required fields!")

def show_suppliers():
    st.header("Suppliers Management")
    
    tab1, tab2 = st.tabs(["Supplier List", "Add Supplier"])
    
    session = get_session()
    
    with tab1:
        suppliers = session.query(Supplier).all()
        if suppliers:
            df = pd.DataFrame([{
                "ID": s.id,
                "Name": s.name,
                "Contact Person": s.contact_person,
                "Email": s.email,
                "Phone": s.phone,
                "Address": s.address
            } for s in suppliers])
            st.dataframe(df)
    
    with tab2:
        name = st.text_input("Supplier Name")
        contact_person = st.text_input("Contact Person")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        address = st.text_area("Address")
        
        if st.button("Add Supplier"):
            if name:
                new_supplier = Supplier(
                    name=name,
                    contact_person=contact_person,
                    email=email,
                    phone=phone,
                    address=address
                )
                session.add(new_supplier)
                session.commit()
                st.success("Supplier added successfully!")
            else:
                st.error("Please fill in all required fields!")

def show_orders():
    st.header("Orders Management")
    
    tab1, tab2 = st.tabs(["Order List", "Create Order"])
    
    session = get_session()
    
    with tab1:
        orders = session.query(Order).all()
        if orders:
            df = pd.DataFrame([{
                "Order ID": o.id,
                "Date": o.order_date,
                "Status": o.status,
                "Total Amount": o.total_amount
            } for o in orders])
            st.dataframe(df)
            
            # View order details
            order_id = st.number_input("Enter Order ID to view details", min_value=1)
            if st.button("View Details"):
                order = session.query(Order).filter_by(id=order_id).first()
                if order:
                    st.write("Order Items:")
                    items_df = pd.DataFrame([{
                        "Product": item.product.name,
                        "Quantity": item.quantity,
                        "Unit Price": item.unit_price,
                        "Total": item.quantity * item.unit_price
                    } for item in order.order_items])
                    st.dataframe(items_df)
                else:
                    st.error("Order not found!")
    
    with tab2:
        st.subheader("Create New Order")
        products = session.query(Product).all()
        
        # Create a form for order items
        product_name = st.selectbox("Select Product", [p.name for p in products])
        quantity = st.number_input("Quantity", min_value=1)
        
        if st.button("Create Order"):
            product = session.query(Product).filter_by(name=product_name).first()
            if product and quantity <= product.quantity:
                # Create order
                new_order = Order(
                    status="completed",
                    total_amount=product.price * quantity
                )
                session.add(new_order)
                session.flush()
                
                # Create order item
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.price
                )
                session.add(order_item)
                
                # Update product quantity
                product.quantity -= quantity
                
                session.commit()
                st.success("Order created successfully!")
            else:
                st.error("Invalid product or insufficient stock!")

if __name__ == "__main__":
    main()