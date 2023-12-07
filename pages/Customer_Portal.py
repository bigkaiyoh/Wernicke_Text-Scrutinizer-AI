import streamlit as st
import stripe

stripe.api_key = st.secrets.stripe_api_key

st.set_page_config(
    page_title = "Customer Portal",
    page_icon = "🧠",
)

def main():
    #language switch toggle
    JP = st.toggle("Japanese (日本語)")
    if JP:
        st.title('カスタマーポータル')
        # ユーザーに支払い時に使用したメールアドレスを尋ねる
        email = st.text_input('支払い時に使用したメールアドレスを入力してください：')
        if email:
            # Stripe APIを使用してメールで顧客IDを取得する
            customers = stripe.Customer.list(email=email).data

            # そのメールアドレスの顧客がいない場合、警告を表示する
            if len(customers) == 0:
                st.error('指定されたメールアドレスの顧客が見つかりません。メールアドレスを確認して再試行するか、サポートにお問い合わせください。')
            else:
                # 返される最初の顧客が求めているものであると仮定します
                customer_id = customers[0].id

                # 請求ポータルセッションを作成
                session = stripe.billing_portal.Session.create(
                    customer=customer_id,
                    return_url=st.secrets["redirect_url"]
                )
                
                # 請求ポータルへのリンクを提供
                st.markdown(f"請求情報は[こちら]({session.url})で管理できます。", unsafe_allow_html=True)
        else:
            st.warning("続行するにはメールアドレスを入力してください。")

        st.write("""\n
            ### できること:

            **プランの管理:**
            - サブスクリプションプランを表示および変更します。
            - サブスクリプションをアップグレード、ダウングレード、またはキャンセルします。

            **アカウント情報の変更:**
            - 名前、メールアドレス、および支払い方法の更新。\n
            """)
        st.error("非Googleアカウントでの支払いの場合、アプリを使用するためにはメールアドレスをポータル経由でGoogleアカウントに更新してください。")
    else:
        st.title('Customer Portal')

        # Ask the user for their email used during the payment
        email = st.text_input('Please enter the email address used during payment:')
        
        if email:
            # Retrieve Stripe Customer ID using Stripe API by searching for customers with email
            customers = stripe.Customer.list(email=email).data

            # If there are no customers with that email, show a warning.
            if len(customers) == 0:
                st.error('No customer found with the provided email. Please check the email and try again, or contact support.')
            else:
                # Assuming the first customer returned is the one we're looking for
                customer_id = customers[0].id

                # Create a billing portal session
                session = stripe.billing_portal.Session.create(
                    customer=customer_id,
                    return_url=st.secrets["redirect_url"]
                )
                
                # Provide a link to the billing portal
                st.markdown(f"You can manage your billing information [here]({session.url}).", unsafe_allow_html=True)
        else:
            st.warning("Please enter the email address to proceed.")

        st.write("""\n
            ### What You Can Do:

            **Manage Your Plan:**
            - View and modify your subscription plan.
            - Upgrade, downgrade, or cancel your subscription.

            **Modify Your Account Information:**
            - Update your name, email, and the method of payment.\n
            """)
        st.error("If your payment was made with a non-Google account, please update to a Google account through the portal to use the app.")
# Run the customer portal function if this file is executed.
if __name__ == "__main__":
    main()