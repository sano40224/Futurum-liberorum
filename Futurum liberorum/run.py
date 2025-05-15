from flask import Flask , render_template , jsonify , request, session , json,redirect, url_for ,flash
import requests
import os 
import random
import string
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
#mysql-connector-pythonの読み込み
import mysql.connector

app = Flask(__name__)


#暗号化/復号化するためのキー設定(キーは任意の文字列)
app.secret_key = 'abcdefghijkmn'

# APIエンドポイント（例: ZipCloud API）
ZIPCODE_API_URL = "https://zipcloud.ibsnet.co.jp/api/search"

okImage= {'png', 'jpg', 'jpeg'}

# ランダムな6文字の文字列を生成する関数
def generate_random_string(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

#db接続関数
def conn_db():
    conn = mysql.connector.connect(
        host = "127.0.0.1",
        user = "root",
        password = "root",
        db = "ih22db",
        charset="utf8" ,
        use_unicode=True
    )
    conn.cursor(dictionary=True)
    return conn


#アカウント新規作成
@app.route('/insert_account', methods=['POST'])
def insert_db():
    con = conn_db()
    cur = con.cursor()

#00001から順にアカウントIDを作成する
    cur.execute("SELECT MAX(accountId) FROM t_account")
    max_id = cur.fetchone()[0]
    if max_id:
        new_account_id = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        new_account_id = "00001"  # 初回は"00001"から始める

    #入力画面から値の受け取り
    strMailadress = request.form.get('email')
    strPass = request.form.get('password')
    strName = request.form.get('name')
    strName_first = request.form.get('name_first')
    strName_kana = request.form.get('name_kana')
    strName_kana_first = request.form.get('name_kana_first')
    strUsername = request.form.get('username')
    strBirthday = request.form.get('birthday')
    strGender = request.form.get('gender')
    strPhone = request.form.get('phone')
    strChildren_count = request.form.get('children_count')
    password_confirm = request.form.get('password_confirm')

    # エラーを格納する辞書
    errors = {}

    # usernameの存在確認
    cur.execute("SELECT accountId FROM t_account WHERE accountName = %s", (strUsername,))
    existing_user = cur.fetchone()
    if existing_user:
        # usernameが既に存在する場合、エラーメッセージを表示
        errors["username"] = "このユーザー名は既に使用されています。別のユーザー名をお試しください。"

    # メールアドレスの重複チェック
    cur.execute("SELECT accountId FROM t_account WHERE emailAddress = %s", (strMailadress,))
    if cur.fetchone():
        errors["email"] = "メールアドレスは既に使われています。"

    # パスワードのバリデーション
    password_pattern = r"^(?=.*[a-zA-Z])(?=.*\d).{8,}$"
    if not re.match(password_pattern, strPass):
        errors["password"] = "パスワードは半角英数字を含む8文字以上で構成してください。"
    elif strPass != password_confirm:
        errors["password_confirm"] = "パスワードが一致しません。"

    # 名前のバリデーション（漢字、ひらがな、カタカナのみ）
    name_pattern = r'^[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]+$'
    if not re.match(name_pattern, strName_first) or not re.match(name_pattern, strName):
        errors["name"] = "姓名は漢字、ひらがな、カタカナにしてください。"

    # 名前カナのバリデーション（カタカナのみ）
    kana_pattern = r'^[\u30A0-\u30FF]+$'
    if not re.match(kana_pattern, strName_kana_first) or not re.match(kana_pattern, strName_kana):
        errors["name_kana"] = "姓名カナはカタカナにしてください。"

    # 誕生日のバリデーション
    try:
        datetime.strptime(strBirthday, "%Y/%m/%d")
    except ValueError:
        errors["birthday"] = "無効な日付形式です。"
    
    # エラーがある場合はテンプレート再表示
    if errors:
        return render_template('register.html', errors=errors)

    icon = "./static/images\default_icon.jpg"
    
    # データの挿入
    sql = """
        INSERT INTO t_account (
            accountId, accountName, icon, emailAddress, password, lastname, firstname, lastnamekana,
            firstnamekana, birthDate, gender, phonenumber, numberofchildren, points
        ) VALUES (
            %(account_id)s, %(accountName)s, %(icon)s, %(email)s, %(password)s, %(name)s, %(name_first)s,
            %(name_kana)s, %(name_kana_first)s, %(birthday)s, %(gender)s, %(phone)s, %(children_count)s, 0
        )
    """
    data = {
        'account_id': new_account_id,
        'icon': icon,
        'email': strMailadress,
        'password': strPass,
        'name': strName,
        'name_first': strName_first,
        'name_kana': strName_kana,
        'name_kana_first': strName_kana_first,
        'accountName': strUsername,
        'birthday': strBirthday,
        'gender': strGender,
        'phone': strPhone,
        'children_count': strChildren_count,
    }
    cur.execute(sql, data)
    
    #00001から順にアカウントIDを作成する
    cur.execute("SELECT MAX(addressId) FROM t_address")
    max_id = cur.fetchone()[0]
    if max_id:
        addressId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        addressId = "00001"  # 初回は"00001"から始める
        

    #入力画面から値の受け取り
    postalCode = request.form.get('postal_code')
    prefecture = request.form.get('address')
    cityWard = request.form.get('city')
    addressNumber = request.form.get('street')
    buildingName = request.form.get('building')
        
        
    # データの挿入
    sql = """
        INSERT INTO t_address (
            addressId, accountId, postalCode, prefecture, cityWard, addressNumber, buildingName
        ) VALUES (
            %(addressId)s, %(accountId)s, %(postalCode)s, %(prefecture)s, %(cityWard)s, %(addressNumber)s, %(buildingName)s
        )
    """
    
    data = {
        'addressId': addressId,
        'accountId': new_account_id,
        'postalCode': postalCode,
        'prefecture': prefecture,
        'cityWard': cityWard,
        'addressNumber': addressNumber,
        'buildingName': buildingName
    }
    
    cur.execute(sql, data)

    # データベースの変更を確定
    con.commit()
    con.close()
    cur.close()

    # 成功時のリダイレクト
    return render_template('login.html')

# パスワード更新
@app.route('/update_pass')
def update_pass():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
        
    return render_template("update_pass.html")
    
# パスワード更新処理
@app.route('/submit_pass', methods=['POST'])
def submit_pass():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
    
    
    con = conn_db()
    cur = con.cursor()


    #実行したいSQLの作成
    sql = " SELECT * from t_account WHERE accountId = %s"
    cur.execute(sql, (accountId,))
    rows = cur.fetchall()
    
    # データがある場合のみ処理
    if rows:
        dbPass = rows[0][9]  # 最初のレコードのパスワードを取得
        
    
    #入力画面から値の受け取り
    nowPassword = request.form.get('nowPassword')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')
    
    
    # エラーを格納する辞書
    errors = {}
    
    if nowPassword != dbPass:
        errors["nowPassword"] = "現在のパスワードが間違っています。"
    
    # パスワードのバリデーション
    password_pattern = r"^(?=.*[a-zA-Z])(?=.*\d).{8,}$"
    if not re.match(password_pattern, password):
        errors["password"] = "パスワードは半角英数字を含む8文字以上で構成してください。"
        
    elif password != password_confirm:
        errors["password_confirm"] = "パスワードが一致しません。"
        
    
    
    # エラーがある場合はテンプレート再表示
    if errors:
        con.close()
        cur.close()
        return render_template('update_pass.html', errors=errors)
    
    else:
        # データの挿入
        sql = """
            UPDATE t_account
            SET 
                password = %(password)s
            WHERE accountId = %(accountId)s
        """
        
        data = {
            'password': password,
            'accountId': accountId
        }
        
        cur.execute(sql, data)


        # データベースの変更を確定
        accountId = session.get("login_id")
        sql = " SELECT points FROM t_account WHERE accountId = %s "
        cur.execute(sql, (accountId,))
        result = cur.fetchone()
        point = result[0] if result else 0
        con.commit()
        con.close()
        cur.close()
        

        # 成功時のリダイレクト
        return render_template('top.html',point=point)


# 登録情報閲覧
@app.route('/show_address')
def show_address():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
    
    
    con = conn_db()
    cur = con.cursor()
    
    #実行したいSQLの作成
    sql = " SELECT * from t_account WHERE accountId = %s"
    cur.execute(sql, (accountId,))
    rows = cur.fetchall()
    #配列の生成
    account_datas = []
    
    for row in rows:
        account_datas.append({"accountName": row[1], "numberOfChildren": row[8], "phoneNumber":row[17]})
        
        
    #実行したいSQLの作成
    sql = " SELECT * from t_address WHERE accountId = %s"
    cur.execute(sql, (accountId,))
    rows = cur.fetchall()
    print(rows)
    #配列の生成
    address_datas = []
    
    for row in rows:
        address_datas.append({"postalCode": row[2], "prefecture": row[3], "cityWard":row[4], "addressNumber":row[5], "buildingName":row[6]})
    
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    accountId = session.get("login_id")
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #curの終了
    cur.close()
    #conの終了
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("show_address.html", aryData=aryData , point=point, account_datas=account_datas,address_datas=address_datas)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

# 登録情報更新
@app.route('/update_address')
def update_address():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
    
    
    con = conn_db()
    cur = con.cursor()
    
    #実行したいSQLの作成
    sql = " SELECT * from t_account WHERE accountId = %s"
    cur.execute(sql, (accountId,))
    rows = cur.fetchall()
    #配列の生成
    account_datas = []
    
    for row in rows:
        account_datas.append({"accountName": row[1], "numberOfChildren": row[8], "phoneNumber":row[17]})
        
        
    #実行したいSQLの作成
    sql = " SELECT * from t_address WHERE accountId = %s"
    cur.execute(sql, (accountId,))
    rows = cur.fetchall()
    #配列の生成
    address_datas = []
    
    for row in rows:
        address_datas.append({"postalCode": row[2], "prefecture": row[3], "cityWard":row[4], "addressNumber":row[5], "buildingName":row[6]})
    
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    accountId = session.get("login_id")
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #curの終了
    cur.close()
    #conの終了
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("update_address.html", aryData=aryData , point=point, account_datas=account_datas,address_datas=address_datas)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

# 登録情報更新処理
@app.route('/submit_address', methods=['POST'])
def submit_address():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
    
    
    con = conn_db()
    cur = con.cursor()

    #入力画面から値の受け取り
    strUsername = request.form.get('username')
    strPhone = request.form.get('phone')
    strChildren_count = request.form.get('children_count')
    postalCode = request.form.get('postal_code')
    prefecture = request.form.get('address')
    cityWard = request.form.get('city')
    addressNumber = request.form.get('street')
    buildingName = request.form.get('building')
    
    
    #配列の生成
    account_datas = []
    account_datas.append({"accountName": strUsername, "numberOfChildren": strChildren_count, "phoneNumber":strPhone})
    address_datas = []
    address_datas.append({"postalCode": postalCode, "prefecture": prefecture, "cityWard": cityWard, "addressNumber": addressNumber, "buildingName": buildingName})
        
    # エラーを格納する辞書
    errors = {}

    # usernameの存在確認
    cur.execute("SELECT accountId FROM t_account WHERE accountName = %s AND accountId != %s", (strUsername, accountId))
    existing_user = cur.fetchone()
    if existing_user:
        # usernameが既に存在する場合、エラーメッセージを表示
        errors["username"] = "このユーザー名は既に使用されています。別のユーザー名をお試しください。"

    
    
    # エラーがある場合はテンプレート再表示
    if errors:
        return render_template('update_address.html', errors=errors, account_datas=account_datas, address_datas=address_datas)

    # データの挿入
    sql = """
        UPDATE t_account
        SET 
            accountName = %(accountName)s,
            phonenumber = %(phone)s,
            numberofchildren = %(children_count)s
        WHERE accountId = %(accountId)s
    """
    
    data = {
        'accountName': strUsername,
        'phone': strPhone,
        'children_count': strChildren_count,
        'accountId': accountId
    }
    
    cur.execute(sql, data)
        

        
        
    # データの挿入
    sql = """
        UPDATE t_address
        SET 
            postalCode = %(postalCode)s,
            prefecture = %(prefecture)s,
            cityWard = %(cityWard)s,
            addressNumber = %(addressNumber)s,
            buildingName = %(buildingName)s
        WHERE accountId = %(accountId)s
    """
    
    data = {
        'postalCode': postalCode,
        'prefecture': prefecture,
        'cityWard': cityWard,
        'addressNumber': addressNumber,
        'buildingName': buildingName,
        'accountId': accountId
    }

    cur.execute(sql, data)

    sql = " SELECT points FROM t_account WHERE accountId = %s "
    accountId = session.get("login_id")
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    # データベースの変更を確定
    con.commit()
    con.close()
    cur.close()
    

    # 成功時のリダイレクト
    return redirect(url_for("profile", searchId=accountId , point=point))

#郵便番号検索
@app.route('/get_address', methods=['GET'])
def get_address():
    zipcode = request.args.get('zipcode')
    if not zipcode:
        return jsonify({"error": "郵便番号が必要です"}), 400
    
    # 郵便番号APIにリクエストを送信
    response = requests.get(ZIPCODE_API_URL, params={"zipcode": zipcode})
    if response.status_code != 200:
        return jsonify({"error": "APIリクエストに失敗しました"}), 500

    data = response.json()
    if data['results'] is None:
        return jsonify({"error": "郵便番号が見つかりません"}), 404

    # 結果を返す
    result = data['results'][0]
    return jsonify({
        "prefecture": result['address1'],
        "city": result['address2'],
        "town": result['address3']
    })

#新規出品（sale）
@app.route('/insert_sale', methods = ['POST'])
def insert_sale():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
    
    
    #入力画面から値の受け取り
    file = request.files["upload1"]
    
    # ファイル選択のチェック
    if file.filename == "":
        return render_template("display_form.html", error_message="画像を選択してください。")
    
    
    for i in range(1, 4):
        # ファイルオブジェクトを取得
        file = request.files.get(f'upload{i}')

        # ファイルが選択されているか確認
        if file and file.filename:
            # ファイル名の拡張子を取得
            file_extension = file.filename.split('.')[-1].lower()

            # 拡張子が許可された形式かどうかをチェック
            if file_extension not in okImage:
                return render_template("display_form.html", error_message="許可されていないファイル形式です。")
    
    
    
    con = conn_db()
    cur = con.cursor()
    
    
    #00001から順にPKを作成する
    cur.execute("SELECT MAX(saleId) FROM t_sale")
    max_id = cur.fetchone()[0]
    if max_id:
        saleId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        saleId = "00001"  # 初回は"00001"から始める
    
    
    #入力画面から値の受け取り
    productName = request.form.get('productName')
    productCondition = request.form.get('productCondition')
    productDescription = request.form.get('productDescription')
    sellingPrice = request.form.get('sellingPrice')
    categoryId = request.form.get('categoryId')
    shippingPayer = request.form.get('shippingPayer')
    shippingEstimate = request.form.get('shippingEstimate')
    
    
    # 「¥」とカンマを取り除く
    sellingPrice = sellingPrice.replace('¥', '').replace(',', '')
    
    
    #金額の型変更
    sellingPrice = Decimal(sellingPrice)
    
    #価格が不正な場合にエラー
    if sellingPrice < 300 or sellingPrice > 9999999:
        con.close()
        cur.close()
        error_message = "販売価格は¥300～9,999,999の間で設定してください。"
        errors = {"price": error_message}
        return render_template('display_form.html', errors=errors)
    
    
    # SQL文
    sql = """
        INSERT INTO t_sale (
            saleId, accountId, productName, productCondition, productDescription, sellingPrice,
            categoryId, shippingPayer, shippingEstimate, listingDateTime, listingStatus, deletionStatus
        ) VALUES (
            %(saleId)s, %(accountId)s, %(productName)s, %(productCondition)s, %(productDescription)s,
            %(sellingPrice)s, %(categoryId)s, %(shippingPayer)s, %(shippingEstimate)s, %(listingDateTime)s,
            %(listingStatus)s, %(deletionStatus)s
        )
    """
 
    # データを辞書で準備
    data = {
        'saleId': saleId,
        'accountId': accountId,
        'productName': productName,
        'productCondition': productCondition,
        'productDescription': productDescription,
        'sellingPrice': sellingPrice,
        'categoryId': categoryId,
        'shippingPayer': shippingPayer,
        'shippingEstimate': shippingEstimate,
        'listingDateTime': datetime.now(),
        'listingStatus': '出品中',
        'deletionStatus': 0
    }
 
    # データベース接続してSQL文を実行
    cur.execute(sql, data)
    
    
    
    # カテゴリSQL
    #00001から順にPKを作成する
    cur.execute("SELECT MAX(saleCategoryStatusId) FROM t_saleCategoryStatus")
    max_id = cur.fetchone()[0]
    if max_id:
        saleCategoryStatusId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        saleCategoryStatusId = "00001"  # 初回は"00001"から始める
        
        
    #入力画面から値の受け取り
    categoryId = request.form.get('categoryId')
    
    # SQL文
    sql = """
        INSERT INTO t_saleCategoryStatus (
            saleCategoryStatusId, saleId, categoryId
        ) VALUES (
            %(saleCategoryStatusId)s, %(saleId)s, %(categoryId)s
        )
    """
    
    # データを辞書で準備
    data = {
        'saleCategoryStatusId': saleCategoryStatusId,
        'saleId': saleId,
        'categoryId': categoryId,
    }
    
    # データベース接続してSQL文を実行
    cur.execute(sql, data)
    
    

    # 画像アップロード
    for i in range(1,5):
        file = request.files[f"upload{i}"]
            
        # ファイル選択のチェック
        if file.filename != "":
            random_string = generate_random_string()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # YYYYMMDDHHMMSS形式
            filename = f"{accountId}_{timestamp}_{random_string}"
                
            # ファイル(パス)の設定
            path = os.path.join("./static/upload", filename)
                        
            # ファイルの保存
            file.save(path)
            
            
            # 画像SQL
            #00001から順にPKを作成する
            cur.execute("SELECT MAX(salePhotoId) FROM t_salePhoto")
            max_id = cur.fetchone()[0]
            if max_id:
                salePhotoId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
            else:
                salePhotoId = "00001"  # 初回は"00001"から始める
                
                
            #入力画面から値の受け取り
            productPhoto = path
            
            # SQL文
            sql = """
                INSERT INTO t_salePhoto (
                    salePhotoId, saleId, productPhoto
                ) VALUES (
                    %(salePhotoId)s, %(saleId)s, %(productPhoto)s
                )
            """
            
            # データを辞書で準備
            data = {
                'salePhotoId': salePhotoId,
                'saleId': saleId,
                'productPhoto': productPhoto,
            }
            
            # データベース接続してSQL文を実行
            cur.execute(sql, data)
            
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0        
    #データ確定
    con.commit()
    
    con.close()
    cur.close()
    

    return redirect(url_for('search_search',point=point))

#レンタル出品（rental）
@app.route('/insert_rental', methods = ['POST'])
def insert_rental():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
    
    
    #入力画面から値の受け取り
    file = request.files["upload1"]
    
    # ファイル選択のチェック
    if file.filename == "":
        return render_template("display_form_rental.html", error_message="画像を選択してください。")
    
    
    for i in range(1, 4):
        # ファイルオブジェクトを取得
        file = request.files.get(f'upload{i}')

        # ファイルが選択されているか確認
        if file and file.filename:
            # ファイル名の拡張子を取得
            file_extension = file.filename.split('.')[-1].lower()

            # 拡張子が許可された形式かどうかをチェック
            if file_extension not in okImage:
                return render_template("display_form_rental.html", error_message="許可されていないファイル形式です。")
    
    
    
    con = conn_db()
    cur = con.cursor()
    
    
    #00001から順にPKを作成する
    cur.execute("SELECT MAX(rentalId) FROM t_rental")
    max_id = cur.fetchone()[0]
    if max_id:
        rentalId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        rentalId = "00001"  # 初回は"00001"から始める
    
    
    #入力画面から値の受け取り
    productName = request.form.get('productName')
    productCondition = request.form.get('productCondition')
    productDescription = request.form.get('productDescription')
    sellingPrice = request.form.get('sellingPrice')
    categoryId = request.form.get('categoryId')
    shippingPayer = request.form.get('shippingPayer')
    shippingEstimate = request.form.get('shippingEstimate')
    rentalPeriod = request.form.get('rentalPeriod')
    
    
    # 「¥」とカンマを取り除く
    sellingPrice = sellingPrice.replace('¥', '').replace(',', '')
    
    
    #金額の型変更
    sellingPrice = Decimal(sellingPrice)
    
    #価格が不正な場合にエラー
    if sellingPrice < 300 or sellingPrice > 9999999:
        con.close()
        cur.close()
        error_message = "販売価格は¥300～9,999,999の間で設定してください。"
        errors = {"price": error_message}
        return render_template('display_forma_rental.html', errors=errors)
    
    
    # SQL文
    sql = """
        INSERT INTO t_rental (
            rentalId, accountId, rentalProductName, rentalProductCondition, rentalDescription, rentalPrice,
            categoryId, rentalShippingPayer, rentalShippingEstimate, rentalListingDateTime, rentalListingStatus, rentalDeletionStatus,rentalPeriod
        ) VALUES (
            %(rentalId)s, %(accountId)s, %(productName)s, %(productCondition)s, %(productDescription)s,
            %(sellingPrice)s, %(categoryId)s, %(shippingPayer)s, %(shippingEstimate)s, %(listingDateTime)s,
            %(listingStatus)s, %(deletionStatus)s,%(rentalPeriod)s
        )
    """
 
    # データを辞書で準備
    data = {
        'rentalId': rentalId,
        'accountId': accountId,
        'productName': productName,
        'productCondition': productCondition,
        'productDescription': productDescription,
        'sellingPrice': sellingPrice,
        'categoryId': categoryId,
        'shippingPayer': shippingPayer,
        'shippingEstimate': shippingEstimate,
        'listingDateTime': datetime.now(),
        'listingStatus': '出品中',
        'deletionStatus': 0,
        'rentalPeriod':rentalPeriod
    }
 
    # データベース接続してSQL文を実行
    cur.execute(sql, data)
    
    
    
    # カテゴリSQL
    #00001から順にPKを作成する
    cur.execute("SELECT MAX(rentalCategoryStatusId) FROM t_rentalCategoryStatus")
    max_id = cur.fetchone()[0]
    if max_id:
        rentalCategoryStatusId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        rentalCategoryStatusId = "00001"  # 初回は"00001"から始める
        
        
    #入力画面から値の受け取り
    categoryId = request.form.get('categoryId')
    
    # SQL文
    sql = """
        INSERT INTO t_rentalCategoryStatus (
            rentalCategoryStatusId, rentalId, categoryId
        ) VALUES (
            %(rentalCategoryStatusId)s, %(rentalId)s, %(categoryId)s
        )
    """
    
    # データを辞書で準備
    data = {
        'rentalCategoryStatusId': rentalCategoryStatusId,
        'rentalId': rentalId,
        'categoryId': categoryId,
    }
    
    # データベース接続してSQL文を実行
    cur.execute(sql, data)
    
    

    # 画像アップロード
    for i in range(1,5):
        file = request.files[f"upload{i}"]
            
        # ファイル選択のチェック
        if file.filename != "":
            random_string = generate_random_string()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # YYYYMMDDHHMMSS形式
            filename = f"{accountId}_{timestamp}_{random_string}_{file.filename}"
                
            # ファイル(パス)の設定
            path = os.path.join("./static/upload", filename)
                        
            # ファイルの保存
            file.save(path)
            
            
            # 画像SQL
            #00001から順にPKを作成する
            cur.execute("SELECT MAX(rentalPhotoId) FROM t_rentalPhoto")
            max_id = cur.fetchone()[0]
            if max_id:
                rentalPhotoId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
            else:
                rentalPhotoId = "00001"  # 初回は"00001"から始める
                
                
            #入力画面から値の受け取り
            productPhoto = path
            
            # SQL文
            sql = """
                INSERT INTO t_rentalPhoto (
                    rentalPhotoId, rentalId, rentalPhoto
                ) VALUES (
                    %(rentalPhotoId)s, %(rentalId)s, %(rentalPhoto)s
                )
            """
            
            # データを辞書で準備
            data = {
                'rentalPhotoId': rentalPhotoId,
                'rentalId': rentalId,
                'rentalPhoto': productPhoto,
            }
            
            # データベース接続してSQL文を実行
            cur.execute(sql, data)
            
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0       
    #データ確定
    con.commit()
    
    con.close()
    cur.close()
    

    
    return redirect(url_for('search_search_rental',point = point))



@app.route('/')
def index():
    session.clear()
    return render_template('login.html')

#ログイン認証
@app.route('/login_check', methods = ['POST'])
def login_check():
    ary = []
    #login_form.htmlから渡された情報を格納
    strId = request.form.get('mailadress')
    strPass = request.form.get('password')
    strName = request.form.get('mailadress')

    con = conn_db()
    cur = con.cursor()
    sql = " select accountID, accountName, emailAddress , points from t_account where emailAddress = %s and password = %s or accountName = %s and password = %s"
    cur.execute(sql,[strId , strPass , strName , strPass])
    rows = cur.fetchall()
    for row in rows:
        ary.append(row)
        session["login_id"] = row[0]
        session["login_name"] = row[1]

        # aryDataをセッションに保存
    session["aryData"] = json.dumps(ary)  # リストをJSON形式で保存
    
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    accountId = session.get("login_id")
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    if not ary :
        cur.close()
        con.close()
        return render_template("login.html")
    else:
        cur.close()
        con.close()
    return render_template("top.html",aryData=ary,point=point)

#新規登録画面の表示
@app.route('/register')
def search_regi():
    return render_template('register.html')

#商品検索画面(出品)
@app.route('/search')
def search_search():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    #DB連携
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    
    search_txt = request.args.get('search_box', '')
    
    match = re.fullmatch(r"pointGet(\d+)", search_txt)
    if search_txt == "pointReset":
        # データの挿入
            sql = """
                UPDATE t_account
                SET
                points = 0
                WHERE accountId = %s
            """
            cur.execute(sql, (accountId,))
            # データベースの変更を確定
            con.commit()
   
    elif match:
        num = int(match.group(1))  # キャプチャした数字部分を取得
        #実行したいSQLの作成
        sql = " SELECT points FROM t_account WHERE accountId = %s "
        cur.execute(sql, (accountId,))
       
        result = cur.fetchone()
        num = num + result[0]
       
        # 新しいポイントが8桁を超えていないか確認
        if num >= 100000000:  # 8桁を超える場合
            num = 99999999
   
        # データの挿入
        sql = """
            UPDATE t_account
            SET
            points = %s
            WHERE accountId = %s
        """
        cur.execute(sql, (num, accountId))
        # データベースの変更を確定
        con.commit()
            
    # ポイントを反映
    #実行したいSQLの作成
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #実行したいSQLの作成
    sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId GROUP BY s.saleId "#全列の抽出
    cur.execute(sql)
    rows = cur.fetchall()
    #配列の生成
    datas = []
    for row in rows:
        datas.append({"saleId": row[0], "productPhoto": row[-1], "sellingPrice": int(row[6]), "productName" :row[3], "listingStatus" : row[10] ,"deletionStatus":row[11]})
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #curの終了
    cur.close()
    #conの終了
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("search.html", aryData=aryData , datas=datas ,point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

#商品絞り込み画面(出品)
@app.route('/search_icon')
def search_icon():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    #DB連携
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    
    search_txt = request.args.get('search_box', '')
    
    match = re.fullmatch(r"pointGet(\d+)", search_txt)
    if search_txt == "pointReset":
        # データの挿入
            sql = """
                UPDATE t_account
                SET
                points = 0
                WHERE accountId = %s
            """
            cur.execute(sql, (accountId,))
            # データベースの変更を確定
            con.commit()
   
    elif match:
        num = int(match.group(1))  # キャプチャした数字部分を取得
        #実行したいSQLの作成
        sql = " SELECT points FROM t_account WHERE accountId = %s "
        cur.execute(sql, (accountId,))
       
        result = cur.fetchone()
        num = num + result[0]
       
        # 新しいポイントが8桁を超えていないか確認
        if num >= 100000000:  # 8桁を超える場合
            num = 99999999
   
        # データの挿入
        sql = """
            UPDATE t_account
            SET
            points = %s
            WHERE accountId = %s
        """
        cur.execute(sql, (num, accountId))
        # データベースの変更を確定
        con.commit()
    else:
        sql = "SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.productName LIKE %s GROUP BY s.saleId"
        search_txt_sql = f"%{search_txt}%"
        cur.execute(sql ,(search_txt_sql,))
        rows = cur.fetchall()
        #配列の生成
        datas = []
        for row in rows:
            datas.append({"saleId": row[0], "productPhoto": row[-1], "sellingPrice": int(row[6]), "productName" :row[3], "listingStatus" : row[10] ,"deletionStatus":row[11]} )
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    accountId = session.get("login_id")
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #curの終了
    cur.close()
    #conの終了
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("search_icon.html", aryData=aryData , datas=datas , search_txt=search_txt, point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

#商品絞り込み画面(出品)
@app.route('/search_icon_rental')
def search_icon_rental():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    #DB連携
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    
    search_txt = request.args.get('search_box', '')
    
    match = re.fullmatch(r"pointGet(\d+)", search_txt)
    if search_txt == "pointReset":
        # データの挿入
            sql = """
                UPDATE t_account
                SET
                points = 0
                WHERE accountId = %s
            """
            cur.execute(sql, (accountId,))
            # データベースの変更を確定
            con.commit()
   
    elif match:
        num = int(match.group(1))  # キャプチャした数字部分を取得
        #実行したいSQLの作成
        sql = " SELECT points FROM t_account WHERE accountId = %s "
        cur.execute(sql, (accountId,))
       
        result = cur.fetchone()
        num = num + result[0]
       
        # 新しいポイントが8桁を超えていないか確認
        if num >= 100000000:  # 8桁を超える場合
            num = 99999999
   
        # データの挿入
        sql = """
            UPDATE t_account
            SET
            points = %s
            WHERE accountId = %s
        """
        cur.execute(sql, (num, accountId))
        # データベースの変更を確定
        con.commit()
    else:
        sql = "SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalProductName LIKE %s GROUP BY s.rentalId"
        search_txt_sql = f"%{search_txt}%"
        cur.execute(sql ,(search_txt_sql,))
        rows = cur.fetchall()
        #配列の生成
        datas = []
        for row in rows:
            datas.append({"saleId": row[0], "productPhoto": row[-1], "sellingPrice": int(row[6]), "productName" :row[3], "listingStatus" : row[10] ,"deletionStatus":row[11]} )
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    accountId = session.get("login_id")
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #curの終了
    cur.close()
    #conの終了
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("search_icon_rental.html", aryData=aryData , datas=datas , search_txt=search_txt, point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ


#タグ検索
@app.route('/search_tag')
def search_tag():
    tag = request.args.get('tag')
    #DB連携
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    #実行したいSQLの作成
    if tag == "子供服":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.categoryId = 1 GROUP BY s.saleId "#全列の抽出
    elif tag == "ベビー＆マタニティ":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.categoryId = 2 GROUP BY s.saleId "
    elif tag == "育児用品":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.categoryId = 3 GROUP BY s.saleId "
    elif tag == "ベビー用品":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.categoryId = 4 GROUP BY s.saleId "
    elif tag == "新品/未使用":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.productCondition = '新品、未使用' GROUP BY s.saleId "
    elif tag == "未使用に近い":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.productCondition = '未使用に近い' GROUP BY s.saleId "
    elif tag == "目立った汚れなし":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.productCondition = '目立った傷や汚れなし' GROUP BY s.saleId "
    elif tag == "やや傷や汚れあり":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.productCondition = 'やや傷や汚れあり' GROUP BY s.saleId "
    elif tag == "傷/汚れあり":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.productCondition = '傷や汚れあり' GROUP BY s.saleId "
    elif tag == "全体的に状態が悪い":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.productCondition = '全体的に状態が悪い' GROUP BY s.saleId "
    elif tag == "0～1000円":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.sellingPrice between 0 and 1000 GROUP BY s.saleId "
    elif tag == "1000～2000円":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.sellingPrice between 1000 and 2000 GROUP BY s.saleId "
    elif tag == "2000～3000円":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.sellingPrice between 2000 and 3000 GROUP BY s.saleId "
    elif tag == "3000～5000円":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.sellingPrice between 3000 and 5000 GROUP BY s.saleId "
    elif tag == "5000円以上":
        sql = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where s.sellingPrice > 5000 GROUP BY s.saleId "              
    cur.execute(sql)
    rows = cur.fetchall()
    #配列の生成
    datas = []
    for row in rows:
        datas.append({"saleId": row[0], "productPhoto": row[-1], "sellingPrice": int(row[6]), "productName" :row[3], "listingStatus" : row[10] ,"deletionStatus":row[11]} )
        
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    accountId = session.get("login_id")
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #curの終了
    cur.close()
    #conの終了
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("search_tag.html", aryData=aryData , datas=datas , tag=tag , point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ


#商品検索画面(レンタル)
@app.route('/search_rental')
def search_search_rental():

    
    #DB連携
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    #実行したいSQLの作成
    sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId GROUP BY s.rentalId "#全列の抽出
    cur.execute(sql)
    rows = cur.fetchall()
    #配列の生成
    datas = []
    for row in rows:
        datas.append({"rentalId": row[0], "rentalPhoto": row[-1], "rentalPrice": int(row[6]), "rentalName" :row[3], "rentalListingStatus" : row[11] ,"rentalDeletionStatus":row[12]})

    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #curの終了
    print(datas)
    cur.close()
    #conの終了
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("search_rental.html", aryData=aryData , datas=datas ,point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

#商品絞り込み画面(レンタル)
@app.route('/search_tag_rental')
def search_tag_rental():
    tag = request.args.get('tag')
    #DB連携
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    #実行したいSQLの作成
    if tag == "子供服":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.categoryId = 1 GROUP BY s.rentalId "#全列の抽出
    elif tag == "ベビー＆マタニティ":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.categoryId = 2 GROUP BY s.rentalId "
    elif tag == "育児用品":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.categoryId = 3 GROUP BY s.rentalId "
    elif tag == "ベビー用品":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.categoryId = 4 GROUP BY s.rentalId "
    elif tag == "新品/未使用":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalProductCondition = '新品、未使用' GROUP BY s.rentalId "
    elif tag == "未使用に近い":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalProductCondition = '未使用に近い' GROUP BY s.rentalId "
    elif tag == "目立った傷や汚れなし":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalProductCondition = '目立った傷や汚れなし' GROUP BY s.rentalId "
    elif tag == "やや傷や汚れあり":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalProductCondition = 'やや傷や汚れあり' GROUP BY s.rentalId "
    elif tag == "傷/汚れあり":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalProductCondition = '傷や汚れあり' GROUP BY s.rentalId "
    elif tag == "全体的に状態が悪い":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalProductCondition = '全体的に状態が悪い' GROUP BY s.rentalId "
    elif tag == "0～1000円":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalPrice between 0 and 1000 GROUP BY s.rentalId "
    elif tag == "1000～2000円":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalPrice between 1000 and 2000 GROUP BY s.rentalId "
    elif tag == "2000～3000円":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalPrice between 2000 and 3000 GROUP BY s.rentalId "
    elif tag == "3000～5000円":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalPrice between 3000 and 5000 GROUP BY s.rentalId "
    elif tag == "5000円以上":
        sql = " SELECT s.*, MAX(p.rentalPhoto) AS rentalPhoto FROM t_rental AS s LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId where s.rentalPrice > 5000 GROUP BY s.rentalId "              
        
    cur.execute(sql)
    rows = cur.fetchall()
    #配列の生成
    datas = []
    for row in rows:
        datas.append({"rentalId": row[0], "rentalPhoto": row[-1], "rentalPrice": int(row[6]), "rentalName" :row[3], "rentalListingStatus" : row[11] ,"rentalDeletionStatus":row[12]})

    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #curの終了
    cur.close()
    #conの終了
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("search_rental_tag.html", aryData=aryData , datas=datas , tag=tag ,point =point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
#検索処理(出品ID)
@app.route('/search_id')
def search_id():
    # search.htmlから渡された情報を格納
    strId = request.args.get('searchId')
    con = conn_db()
    cur = con.cursor()

    # SQLクエリの作成
    sql_search = """
        SELECT 
            s.*, 
            c.categoryId,
            c.categoryName,
            GROUP_CONCAT(p.productPhoto) AS photos
        FROM t_sale AS s
        LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId
        LEFT JOIN t_category AS c ON s.categoryId = c.categoryId
        WHERE s.saleId = %s
        GROUP BY s.saleId, c.categoryId, c.categoryName;
    """
    # SQL実行
    cur.execute(sql_search, (strId,))  # パラメータ化されたクエリでSQLインジェクション対策
    rows_search = cur.fetchall()
    sql_comment = """
    SELECT 
    c.saleCommentId,
    c.saleId,
    c.accountId,
    c.productCommentContent,
    c.productCommentDeletionStatus,
    a.accountName,
    a.icon
    FROM t_saleComment AS c
    LEFT JOIN t_account AS a ON c.accountId = a.accountId
    WHERE c.saleId = %s;

    """ 
    # SQL実行
    cur.execute(sql_comment, (strId,))
    rows_comment = cur.fetchall()
    
    sql_saler = "SELECT a.accountId, a.accountName, a.icon FROM t_sale AS s INNER JOIN t_account AS a ON s.accountId = a.accountId WHERE s.saleId = %s; "
    cur.execute(sql_saler, (strId,))
    rows_saler = cur.fetchall()
    # 配列の生成
    datas = []
    for row in rows_search:
        # データを辞書型で格納
        data = {
            "saleId": row[0],
            "accountId":row[1],
            "productPhoto": row[-1],
            "sellingPrice": int(row[6]),
            "productExp":row[5],
            "productStatus":row[4],
            "productName": row[3],
            "shippingPayer":row[7],
            "shippingEstimate":row[8],
            "category":row[-2],
            "listingStatus": row[10]
        }

        # productPhoto をリスト化して追加
        if data["productPhoto"]:
            data["photoList"] = data["productPhoto"].split(",")
        else:
            data["photoList"] = []

        datas.append(data)

    comments = []
    for row in rows_comment:
        data_comment = {
            "accountName": row[-2],
            "comment": row[3]
        }
        comments.append(data_comment)
    
    comment_count = len(comments)

    saler_exp =[]
    for row in rows_saler:
        data_saler = {
            "accountId":row[0],
            "accountName":row[1],
            "icon":row[2]
        }
        saler_exp.append(data_saler)

    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    # 接続を閉じる
    cur.close()
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("item_detail.html", aryData=aryData , datas=datas , comments = comments , comment_count=comment_count ,point=point ,data_saler=data_saler)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

#検索処理(レンタルID)
@app.route('/search_id_rental')
def search_id_rental():
    # search.htmlから渡された情報を格納
    strId = request.args.get('searchId')
    con = conn_db()
    cur = con.cursor()

    # SQLクエリの作成
    sql_search = """
        SELECT 
            s.*, 
            c.categoryId,
            c.categoryName,
            GROUP_CONCAT(p.rentalPhoto) AS photos
        FROM t_rental AS s
        LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId
        LEFT JOIN t_category AS c ON s.categoryId = c.categoryId
        WHERE s.rentalId = %s
        GROUP BY s.rentalId, c.categoryId, c.categoryName;
    """
    # SQL実行
    cur.execute(sql_search, (strId,))  # パラメータ化されたクエリでSQLインジェクション対策
    rows_search = cur.fetchall()
    sql_comment = """
    SELECT 
    c.rentalCommentId,
    c.rentalId,
    c.accountId,
    c.rentalCommentContent,
    c.rentalCommentDeletionStatus,
    a.accountName,
    a.icon
    FROM t_rentalComment AS c
    LEFT JOIN t_account AS a ON c.accountId = a.accountId
    WHERE c.rentalId = %s;

    """ 
    # SQL実行
    cur.execute(sql_comment, (strId,))
    rows_comment = cur.fetchall()
    
    sql_saler = "SELECT a.accountId, a.accountName, a.icon FROM t_rental AS s INNER JOIN t_account AS a ON s.accountId = a.accountId WHERE s.rentalId = %s; "
    cur.execute(sql_saler, (strId,))
    rows_saler = cur.fetchall()
    # 配列の生成
    datas = []
    for row in rows_search:
        # データを辞書型で格納
        data = {
            "rentalId": row[0],
            "accountId":row[1],
            "rentalPhoto": row[-1],
            "rentalPrice": int(row[6]),
            "productExp":row[5],
            "productStatus":row[4],
            "productName": row[3],
            "shippingPayer":row[7],
            "shippingEstimate":row[8],
            "category":row[-2],
            "listingStatus": row[11],
            "rentalDeletionStatus":row[12],
            "rentalPeriod":row[9]
        }

        # productPhoto をリスト化して追加
        if data["rentalPhoto"]:
            data["photoList"] = data["rentalPhoto"].split(",")
        else:
            data["photoList"] = []

        datas.append(data)

    comments = []
    for row in rows_comment:
        data_comment = {
            "accountName": row[-2],
            "comment": row[3]
        }
        comments.append(data_comment)
    
    comment_count = len(comments)
    
    saler_exp =[]
    for row in rows_saler:
        data_saler = {
            "accountId":row[0],
            "accountName":row[1],
            "icon":row[2]
        }
        saler_exp.append(data_saler)
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    # 接続を閉じる
    cur.close()
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("item_detail_rental.html", aryData=aryData , datas=datas , comments = comments , comment_count=comment_count, point=point ,data_saler=data_saler)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
    
#購入機能(出品)
@app.route('/product_buy', methods=['POST'])
def product_buy():
    sale_id = request.form.get('saleId')
    account_id =  request.form.get('account_id')
    payMethod = request.form.get('payMethod')
    sellingPrice = request.form.get('sellingPrice')
    account_point = request.form.get('point')
    con = conn_db()
    cur = con.cursor()
    #出品者検索
    cur.execute("SELECT accountId FROM t_sale WHERE saleId = %s", (sale_id,))
    seller_id = cur.fetchone()[0] 

    if payMethod == "ポイント" and int(account_point) < int(sellingPrice):
        flash("ポイントが足りません", "error")
        accountId = session.get("login_id")
        sql = " SELECT points FROM t_account WHERE accountId = %s "
        cur.execute(sql, (accountId,))
        result = cur.fetchone()
        point = result[0] if result else 0
        return redirect(url_for('search_id', searchId=sale_id ,point=point))
    
    #00001から順にsaleTransactionIDを作成する
    cur.execute("SELECT MAX(saleTransactionId) FROM t_saleTransaction")
    max_id = cur.fetchone()[0]
    if max_id:
        new_saleTransaction_id = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        new_saleTransaction_id = "00001"  # 初回は"00001"から始める
        
    # ポイント更新
    point_up_sql = "UPDATE t_account SET points = points + %s WHERE accountId = %s"
    point_down_sql = "UPDATE t_account SET points = points - %s WHERE accountId = %s"
    update_sql = "UPDATE t_sale SET listingStatus = '購入済み' WHERE saleId = %s"
    insert_sql = """
    INSERT INTO t_saleTransaction 
    (saleTransactionId, saleId, accountId, productPaymentMethod, productTransactionStatus)
    VALUES (%s, %s, %s, %s, '0')"""

    cur.execute(point_up_sql,[sellingPrice, seller_id])
    if payMethod == "ポイント":
        cur.execute(point_down_sql,[sellingPrice, account_id])
    cur.execute(update_sql,[sale_id])
    cur.execute(insert_sql,[new_saleTransaction_id , sale_id , account_id , payMethod])

    con.commit()
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    con.close()
    cur.close()
    if "aryData" in session:
        return redirect(url_for('compPage',point=point))
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

#購入機能(レンタル)
@app.route('/product_rental', methods=['POST'])
def product_rental():
    rentalId = request.form.get('rentalId')
    account_id =  request.form.get('account_id')
    payMethod = request.form.get('payMethod')
    sellingPrice = request.form.get('sellingPrice')
    account_point = request.form.get('point')
    con = conn_db()
    cur = con.cursor()
    #出品者検索
    cur.execute("SELECT accountId FROM t_rental WHERE rentalId = %s", (rentalId,))
    seller_id = cur.fetchone()[0] 

    if payMethod == "ポイント" and int(account_point) < int(sellingPrice):
        flash("ポイントが足りません", "error")
        accountId = session.get("login_id")
        sql = " SELECT points FROM t_account WHERE accountId = %s "
        cur.execute(sql, (accountId,))
        result = cur.fetchone()
        point = result[0] if result else 0
        return redirect(url_for('search_id', searchId=rentalId ,point=point))
    
    #00001から順にrentalTransactionIDを作成する
    cur.execute("SELECT MAX(rentalTransactionId) FROM t_rentalTransaction")
    max_id = cur.fetchone()[0]
    if max_id:
        new_rentalTransaction_id = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        new_rentalTransaction_id = "00001"  # 初回は"00001"から始める
        
    # ポイント更新
    point_up_sql = "UPDATE t_account SET points = points + %s WHERE accountId = %s"
    point_down_sql = "UPDATE t_account SET points = points - %s WHERE accountId = %s"
    update_sql = "UPDATE t_rental SET rentalListingStatus = '購入済み' WHERE rentalId = %s"
    insert_sql = """
    INSERT INTO t_rentalTransaction 
    (rentalTransactionId, rentalId, accountId, rentalPaymentMethod, rentalTransactionStatus)
    VALUES (%s, %s, %s, %s, '0')"""

    cur.execute(point_up_sql,[sellingPrice, seller_id])
    if payMethod == "ポイント":
        cur.execute(point_down_sql,[sellingPrice, account_id])
    cur.execute(update_sql,[rentalId])
    cur.execute(insert_sql,[new_rentalTransaction_id , rentalId , account_id , payMethod])

    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    con.commit()

    con.close()
    cur.close()
    if "aryData" in session:
        return redirect(url_for('compPage',point=point))
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

#商品削除
@app.route('/delete_buy', methods=['POST'])
def delete_buy():
    sale_id = request.form.get('saleId')
    con = conn_db()
    cur = con.cursor()
    
    sql = "update t_sale set deletionStatus = 1 where saleId = %s"
    cur.execute(sql,[sale_id])
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    con.commit()

    con.close()
    cur.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return redirect(url_for('search_search', aryData=aryData ,point=point))
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
    
#商品削除
@app.route('/delete_rental', methods=['POST'])
def delete_rental():
    rental_id = request.form.get('rentalId')
    con = conn_db()
    cur = con.cursor()
    
    sql = "update t_rental set rentalDeletionStatus = 1 where rentalId = %s"
    cur.execute(sql,[rental_id])
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    con.commit()

    con.close()
    cur.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return redirect(url_for('search_search_rental', aryData=aryData ,point=point))
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ   
#コメント機能(購入)
@app.route('/comment_buy', methods=['POST'])
def product_comment():
    sale_id = request.form.get('saleId')
    account_id =  request.form.get('account_id')
    comment = request.form.get('comment')
    search_id = sale_id

    con = conn_db()
    cur = con.cursor() 
    #00001から順にアカウントIDを作成する
    cur.execute("SELECT MAX(saleCommentId) FROM t_saleComment")
    max_id = cur.fetchone()[0]
    if max_id:
        new_saleCommentId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        new_saleCommentId = "00001"  # 初回は"00001"から始める
    
    insert_sql = """
    INSERT INTO t_saleComment 
    (saleCommentId, saleId, accountId, productCommentContent, productCommentDeletionStatus)
    VALUES (%s, %s, %s, %s, '0')"""

    cur.execute(insert_sql,[new_saleCommentId , sale_id , account_id , comment])
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    con.commit()

    con.close()
    cur.close()
    if "aryData" in session:
        return redirect(url_for('search_id', searchId=search_id ,point=point))
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
    
#コメント機能(購入)
@app.route('/comment_rental', methods=['POST'])
def rental_comment():
    rental_id = request.form.get('rentalId')
    account_id =  request.form.get('account_id')
    comment = request.form.get('comment')
    search_id = rental_id

    con = conn_db()
    cur = con.cursor() 
    #00001から順にアカウントIDを作成する
    cur.execute("SELECT MAX(rentalCommentId) FROM t_rentalComment")
    max_id = cur.fetchone()[0]
    if max_id:
        new_rentalCommentId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        new_rentalCommentId = "00001"  # 初回は"00001"から始める
    
    insert_sql = """
    INSERT INTO t_rentalComment 
    (rentalCommentId, rentalId, accountId, rentalCommentContent, rentalCommentDeletionStatus)
    VALUES (%s, %s, %s, %s, '0')"""

    cur.execute(insert_sql,[new_rentalCommentId , rental_id , account_id , comment])
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    con.commit()

    con.close()
    cur.close()
    if "aryData" in session:
        return redirect(url_for('search_id_rental', searchId=search_id,point=point))
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
#出品画面(出品)
@app.route('/display_form')
def search_display():
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    
    cur.close()
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("display_form.html", aryData=aryData,point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

#出品画面(レンタル)
@app.route('/display_form_rental')
def search_display_rental():
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成

    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0

    cur.close()
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("display_form_rental.html", aryData=aryData,point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
    
#編集画面(出品)
@app.route('/edit_form')
def edit_form():
    # item_detail.htmlから渡された情報を格納
    strId = request.args.get('searchId')
    con = conn_db()
    cur = con.cursor()

    # SQLクエリの作成
    sql_search = """
        SELECT 
            s.*, 
            c.categoryId,
            c.categoryName,
            GROUP_CONCAT(p.productPhoto) AS photos
        FROM t_sale AS s
        LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId
        LEFT JOIN t_category AS c ON s.categoryId = c.categoryId
        WHERE s.saleId = %s
        GROUP BY s.saleId, c.categoryId, c.categoryName;
    """
    # SQL実行
    cur.execute(sql_search, (strId,))  # パラメータ化されたクエリでSQLインジェクション対策
    rows_search = cur.fetchall()
    sql_comment = """
    SELECT 
    c.saleCommentId,
    c.saleId,
    c.accountId,
    c.productCommentContent,
    c.productCommentDeletionStatus,
    a.accountName,
    a.icon
    FROM t_saleComment AS c
    LEFT JOIN t_account AS a ON c.accountId = a.accountId
    WHERE c.saleId = %s;

    """ 
    # SQL実行
    cur.execute(sql_comment, (strId,))
    rows_comment = cur.fetchall()
    # 配列の生成
    datas = []
    for row in rows_search:
        # データを辞書型で格納
        data = {
            "saleId": row[0],
            "accountId":row[1],
            "productPhoto": row[-1],
            "sellingPrice": int(row[6]),
            "productExp":row[5],
            "productStatus":row[4],
            "productName": row[3],
            "shippingPayer":row[7],
            "shippingEstimate":row[8],
            "category":row[-2],
            "categoryId":row[-3],
            "listingStatus": row[10]
        }

        # productPhoto をリスト化して追加
        if data["productPhoto"]:
            photos = data["productPhoto"].split(",")
            # 各画像を photo1, photo2, ... として格納する
            for index, photo in enumerate(photos, start=1):
                data[f'photo{index}'] = photo
        else:
            # 画像が無い場合は、必要に応じて空文字列や None を設定
            data['photo1'] = ""
            data['photo2'] = ""
            data['photo3'] = ""
            data['photo4'] = ""

        datas.append(data)
    photo_count = len([photo for photo in data["productPhoto"].split(",") if photo.strip() != ""]) if data["productPhoto"] else 0
    comments = []
    for row in rows_comment:
        data_comment = {
            "accountName": row[-2],
            "comment": row[3]
        }
        comments.append(data_comment)
    
    comment_count = len(comments)
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    # 接続を閉じる
    
    cur.close()
    con.close()

    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("edit_form.html", aryData=aryData , datas=datas , comments=comments, comment_count=comment_count, photo_count=photo_count , point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
    
#検索処理(レンタルID)
@app.route('/edit_form_rental')
def edit_form_rental():
    # search.htmlから渡された情報を格納
    strId = request.args.get('searchId')
    con = conn_db()
    cur = con.cursor()

    # SQLクエリの作成
    sql_search = """
        SELECT 
            s.*, 
            c.categoryId,
            c.categoryName,
            GROUP_CONCAT(p.rentalPhoto) AS photos
        FROM t_rental AS s
        LEFT JOIN t_rentalPhoto AS p ON s.rentalId = p.rentalId
        LEFT JOIN t_category AS c ON s.categoryId = c.categoryId
        WHERE s.rentalId = %s
        GROUP BY s.rentalId, c.categoryId, c.categoryName;
    """
    # SQL実行
    cur.execute(sql_search, (strId,))  # パラメータ化されたクエリでSQLインジェクション対策
    rows_search = cur.fetchall()
    sql_comment = """
    SELECT 
    c.rentalCommentId,
    c.rentalId,
    c.accountId,
    c.rentalCommentContent,
    c.rentalCommentDeletionStatus,
    a.accountName,
    a.icon
    FROM t_rentalComment AS c
    LEFT JOIN t_account AS a ON c.accountId = a.accountId
    WHERE c.rentalId = %s;

    """ 
    # SQL実行
    cur.execute(sql_comment, (strId,))
    rows_comment = cur.fetchall()
    # 配列の生成
    datas = []
    for row in rows_search:
        # データを辞書型で格納
        data = {
            "rentalId": row[0],
            "accountId":row[1],
            "rentalPhoto": row[-1],
            "rentalPrice": int(row[6]),
            "productExp":row[5],
            "productStatus":row[4],
            "productName": row[3],
            "shippingPayer":row[7],
            "shippingEstimate":row[8],
            "category":row[-2],
            "categoryId":row[-3],
            "listingStatus": row[11],
            "rentalDeletionStatus":row[12],
            "rentalPeriod":row[9]
        }

        # productPhoto をリスト化して追加
        if data["rentalPhoto"]:
            photos = data["rentalPhoto"].split(",")
            # 各画像を photo1, photo2, ... として格納する
            for index, photo in enumerate(photos, start=1):
                data[f'photo{index}'] = photo
        else:
            # 画像が無い場合は、必要に応じて空文字列や None を設定
            data['photo1'] = ""
            data['photo2'] = ""
            data['photo3'] = ""
            data['photo4'] = ""


        datas.append(data)

    comments = []
    for row in rows_comment:
        data_comment = {
            "accountName": row[-2],
            "comment": row[3]
        }
        comments.append(data_comment)
    
    comment_count = len(comments)
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    # 接続を閉じる
    cur.close()
    con.close()

    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("edit_form_rental.html", aryData=aryData , datas=datas , comments = comments , comment_count=comment_count,point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
    
#出品編集
@app.route('/edit_sale', methods=['POST'])
def edit_sale():
    #入力画面から値の受け取り
    file = request.files["upload1"]

    con = conn_db()
    cur = con.cursor()
    
    saleId = request.form.get('saleId')
    accountId = session.get("login_id")
    productName = request.form.get('productName')
    productCondition = request.form.get('productCondition')
    productDescription = request.form.get('productDescription')
    sellingPrice = request.form.get('sellingPrice')
    shippingPayer = request.form.get('shippingPayer')
    shippingEstimate = request.form.get('shippingEstimate')
    categoryId = request.form.get('categoryId')
    
    # 「¥」とカンマを取り除く
    sellingPrice = sellingPrice.replace('¥', '').replace(',', '')
    
    #金額の型変更
    sellingPrice = Decimal(sellingPrice)
    
    sql = """
            update  t_sale set productName = %(productName)s , productCondition = %(productCondition)s ,
            productDescription = %(productDescription)s,sellingPrice = %(sellingPrice)s , shippingPayer = %(shippingPayer)s,
            shippingEstimate = %(shippingEstimate)s where saleId = %(saleId)s
        """
        
    data = {
        'saleId':saleId,
        'productName': productName,
        'productCondition': productCondition,
        'productDescription': productDescription,
        'sellingPrice': sellingPrice,
        'shippingPayer': shippingPayer,
        'shippingEstimate': shippingEstimate
    }
    
    cur.execute(sql, data)
    
    
    
    # SQL文
    sql = "UPDATE t_saleCategoryStatus SET categoryId = %(categoryId)s WHERE saleId = %(saleId)s"
    
    # データを辞書で準備
    data = {
        'saleId': saleId,
        'categoryId': categoryId,
    }
    
    # データベース接続してSQL文を実行
    cur.execute(sql, data)
    
        # 画像アップロード
    for i in range(1,5):
        file = request.files[f"upload{i}"]
            
        # ファイル選択のチェック
        if file.filename != "":
            random_string = generate_random_string()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # YYYYMMDDHHMMSS形式
            filename = f"{accountId}_{timestamp}_{random_string}_{file.filename}"
            
            # ファイル(パス)の設定
            path = os.path.join("./static/upload", filename)
            
            # ファイルの保存
            file.save(path)
            
            #入力画面から値の受け取り
            productPhoto = path
            
            sql = """
                UPDATE t_salePhoto SET productPhoto = %(productPhoto)s WHERE saleId = %(saleId)s
            """
    
            data = {
                'saleId': saleId,
                'productPhoto': productPhoto,
            }
            
            # データベース接続してSQL文を実行
            cur.execute(sql, data)
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    con.commit()
    
    con.close()
    cur.close()
    
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return redirect(url_for('search_search', aryData=aryData ,point=point))
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

#出品編集(レンタル)
@app.route('/edit_rental', methods=['POST'])
def edit_rental():
    #入力画面から値の受け取り
    file = request.files["upload1"]

    con = conn_db()
    cur = con.cursor()
    
    rentalId = request.form.get('rentalId')
    accountId = session.get("login_id")
    rentalProductName = request.form.get('rentalProductName')
    rentalProductCondition = request.form.get('rentalProductCondition')
    rentalDescription = request.form.get('productDescription')
    rentalPrice = request.form.get('rentalPrice')
    rentalShippingPayer = request.form.get('shippingPayer')
    rentalShippingEstimate = request.form.get('shippingEstimate')
    categoryId = request.form.get('categoryId')
    rentalPeriod = request.form.get('rentalPeriod')
    
    # 「¥」とカンマを取り除く
    rentalPrice = rentalPrice.replace('¥', '').replace(',', '')
    
    #金額の型変更
    rentalPrice = Decimal(rentalPrice)
    
    sql = """
            update  t_rental set rentalProductName = %(rentalProductName)s , rentalProductCondition = %(rentalProductCondition)s ,
            rentalDescription = %(rentalDescription)s, rentalPrice = %(rentalPrice)s , rentalShippingPayer = %(rentalShippingPayer)s,
            rentalShippingEstimate = %(rentalShippingEstimate)s , categoryId = %(categoryId)s , rentalPeriod = %(rentalPeriod)s where rentalId = %(rentalId)s
        """
        
    data = {
        'rentalId':rentalId,
        'rentalProductName': rentalProductName,
        'rentalProductCondition': rentalProductCondition,
        'rentalDescription': rentalDescription,
        'rentalPrice': rentalPrice,
        'rentalShippingPayer': rentalShippingPayer,
        'rentalShippingEstimate': rentalShippingEstimate,
        'rentalPeriod':rentalPeriod,
        'categoryId':categoryId
    }
    
    cur.execute(sql, data)
    
    
    # SQL文
    sql = "UPDATE t_rentalCategoryStatus SET categoryId = %(categoryId)s WHERE rentalId = %(rentalId)s"
    
    # データを辞書で準備
    data = {
        'rentalId': rentalId,
        'categoryId': categoryId,
    }
    
    # データベース接続してSQL文を実行
    cur.execute(sql, data)
    
        # 画像アップロード
    for i in range(1,5):
        file = request.files[f"upload{i}"]
            
        # ファイル選択のチェック
        if file.filename != "":
            random_string = generate_random_string()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # YYYYMMDDHHMMSS形式
            filename = f"{accountId}_{timestamp}_{random_string}_{file.filename}"
            
            # ファイル(パス)の設定
            path = os.path.join("./static/upload", filename)
            
            # ファイルの保存
            file.save(path)
            
            #入力画面から値の受け取り
            productPhoto = path
            
            sql = """
                UPDATE t_rentalPhoto SET rentalPhoto = %(rentalPhoto)s WHERE rentalId = %(rentalId)s
            """
    
            data = {
                'rentalId':rentalId,
                'productPhoto': productPhoto,
            }
            
            # データベース接続してSQL文を実行
            cur.execute(sql, data)
            
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    con.commit()
    
    con.close()
    cur.close()
    
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return redirect(url_for('search_search_rental', aryData=aryData ,point=point))
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
    
# 投稿画面
@app.route('/post')
def post():
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成

    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0

    cur.close()
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("new_post.html", aryData=aryData ,point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ



# 投稿機能
@app.route('/new_post', methods = ['POST'])
def new_post():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
    
    
    for i in range(1, 5):
        # ファイルオブジェクトを取得
        file = request.files.get(f'upload{i}')

        # ファイルが選択されているか確認
        if file and file.filename:
            # ファイル名の拡張子を取得
            file_extension = file.filename.split('.')[-1].lower()

            # 拡張子が許可された形式かどうかをチェック
            if file_extension not in okImage:
                return render_template("new_post.html", error_message="許可されていないファイル形式です。")


    con = conn_db()
    cur = con.cursor()
    
    
    #00001から順にPKを作成する
    cur.execute("SELECT MAX(postId) FROM t_post")
    max_id = cur.fetchone()[0]
    if max_id:
        postId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        postId = "00001"  # 初回は"00001"から始める
    
    
    #入力画面から値の受け取り
    postTitle = request.form.get('postTitle')
    
    
    # SQL文
    sql = """
        INSERT INTO t_post (
            postId, accountId, postTitle, postDateTime, postVisibilityStatus, 
            postDeletionStatus
        ) VALUES (
            %(postId)s, %(accountId)s, %(postTitle)s, %(postDateTime)s, 
            %(postVisibilityStatus)s, %(postDeletionStatus)s
        )
    """
 
 
    # データを辞書で準備
    data = {
        'postId': postId,
        'accountId': accountId,
        'postTitle': postTitle,
        'postDateTime': datetime.now(),
        'postVisibilityStatus': 0,
        'postDeletionStatus': 0
    }
 
 
    # データベース接続してSQL文を実行
    cur.execute(sql, data)
    
    
    # 内容SQL
    for i in range(1,5):
        # 本文SQL
        #00001から順にPKを作成する
        cur.execute("SELECT MAX(postContentId) FROM t_postContent")
        max_id = cur.fetchone()[0]
        if max_id:
            postContentId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
        else:
            postContentId = "00001"  # 初回は"00001"から始める
            
            
        #入力画面から値の受け取り
        postText = request.form.get(f'postContent{i}')
        
        
        # SQL文
        sql = """
            INSERT INTO t_postContent (
                postContentId, postId, postText
            ) VALUES (
                %(postContentId)s, %(postId)s, %(postText)s
            )
        """
        
        
        # データを辞書で準備
        data = {
            'postContentId': postContentId,
            'postId': postId,
            'postText': postText,
        }
        
        
        # データベース接続してSQL文を実行
        cur.execute(sql, data)
        
        
        # 画像SQL
        file = request.files.get(f'upload{i}')
        
        if file and file.filename:
            print("file")
            #00001から順にPKを作成する
            cur.execute("SELECT MAX(postMediaId) FROM t_postMedia")
            max_id = cur.fetchone()[0]
            if max_id:
                postMediaId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
            else:
                postMediaId = "00001"  # 初回は"00001"から始める
                
            random_string = generate_random_string()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # YYYYMMDDHHMMSS形式
            filename = f"{accountId}_{timestamp}_{random_string}_{file.filename}"
                
            # ファイル(パス)の設定
            path = os.path.join("./static/upload", filename)
                        
            # ファイルの保存
            file.save(path)
                
                
            #入力画面から値の受け取り
            postAttachedMedia = path
            
            
            # SQL文
            sql = """
                INSERT INTO t_postMedia (
                    postMediaId, postContentId, postAttachedMedia
                ) VALUES (
                    %(postMediaId)s, %(postContentId)s, %(postAttachedMedia)s
                )
            """
            
            
            # データを辞書で準備
            data = {
                'postMediaId': postMediaId,
                'postContentId': postContentId,
                'postAttachedMedia': postAttachedMedia,
            }
            
            
            # データベース接続してSQL文を実行
            cur.execute(sql, data)
            
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #データ確定
    con.commit()
    
    con.close()
    cur.close()
    
    return redirect(url_for('post_search', postId=postId ,point=point))

#投稿一覧
@app.route('/post_search')
def post_search():
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成    
    
    sql="""SELECT 
    p.postId,
    p.accountId,
    a.accountName,
    p.postTitle,
    p.postDateTime,
    p.postVisibilityStatus,
    p.postDeletionStatus,
    GROUP_CONCAT(DISTINCT c.postContentId) AS postContentIds,
    GROUP_CONCAT(DISTINCT c.postText) AS postTexts,
    GROUP_CONCAT(DISTINCT m.postMediaId) AS postMediaIds,
    GROUP_CONCAT(DISTINCT m.postAttachedMedia) AS attachedMedias
    FROM t_post p
    LEFT JOIN t_account a ON p.accountId = a.accountId
    LEFT JOIN t_postContent c ON p.postId = c.postId
    LEFT JOIN t_postMedia m ON c.postContentId = m.postContentId
    GROUP BY 
    p.postId, p.accountId, a.accountName,
    p.postTitle, p.postDateTime, 
    p.postVisibilityStatus, p.postDeletionStatus;
    """
    
    cur.execute(sql)
    rows = cur.fetchall()
    #配列の生成
    datas = []
    for row in rows:
        datas.append({"postId":row[0],"accountId":row[1], "accountName":row[2],"postTitle":row[3] })
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    cur.close()
    #conの終了
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("post_search.html", aryData=aryData, datas=datas,point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
# 投稿詳細
@app.route('/post_detail')
def post_detail():
    postId = request.args.get('searchId')
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    #実行したいSQLの作成
    sql = """ SELECT 
    p.postId,
    p.accountId,
    a.accountName,
    p.postTitle,
    p.postDateTime,
    p.postVisibilityStatus,
    p.postDeletionStatus,
    GROUP_CONCAT(DISTINCT c.postContentId) AS postContentIds,
    GROUP_CONCAT(DISTINCT c.postText) AS postTexts,
    GROUP_CONCAT(DISTINCT m.postMediaId) AS postMediaIds,
    GROUP_CONCAT(DISTINCT m.postAttachedMedia) AS attachedMedias
    FROM t_post p
    LEFT JOIN t_account a ON p.accountId = a.accountId
    LEFT JOIN t_postContent c ON p.postId = c.postId
    LEFT JOIN t_postMedia m ON c.postContentId = m.postContentId
    WHERE p.postId = %s
    GROUP BY 
    p.postId, p.accountId, a.accountName,
    p.postTitle, p.postDateTime, 
    p.postVisibilityStatus, p.postDeletionStatus;
    """
    cur.execute(sql, (postId,))
    rows = cur.fetchall()
    #配列の生成
    datas = []
    for row in rows:
        datas.append({"postId": row[0], "accountId": row[1],"accountName":row[2] ,"postTitle": row[3], "postText":row[-3],"media":row[-1]})
        
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #curの終了
    cur.close()
    #conの終了
    con.close()
    
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("post_detail.html", aryData=aryData, datas=datas,point=point )
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

#フォローリスト
@app.route('/userlist')
def userlist():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
    
    
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    #実行したいSQLの作成
    sql = " SELECT accountId, accountName FROM t_account WHERE accountId != %s "
    cur.execute(sql, (accountId,))
    rows = cur.fetchall()
    #配列の生成
    datas = []
    for row in rows:
        datas.append({"userId": row[0], "accountName": row[1]})
        
        
    # フォロー中のユーザーIDを取得
    cur.execute("""
    SELECT DISTINCT accountId
    FROM t_follow
    WHERE followerId = %s
    """, (accountId,))
    followed_users = [row[0] for row in cur.fetchall()]
    
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0   
    #curの終了
    cur.close()
    #conの終了
    con.close()
    
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("userlist.html", aryData=aryData, datas=datas, followed_users=followed_users,point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
    


#プロフィール画面
@app.route('/profile')
def profile():
    accountId = request.args.get('searchId')
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成

    
    sql="SELECT accountId, accountName, icon from t_account where accountId = %s "
    cur.execute(sql, (accountId,))
    rows = cur.fetchall()
    #配列の生成
    accounts = []
    for row in rows:
        accounts.append({"accountId":row[0],"accountName":row[1],"icon":row[2],})
    sql_search = " SELECT s.*, MAX(p.productPhoto) AS productPhoto FROM t_sale AS s LEFT JOIN t_salePhoto AS p ON s.saleId = p.saleId where accountId = %s GROUP BY s.saleId "#全列の抽出
    cur.execute(sql_search,(accountId,))
    rows = cur.fetchall()
    #配列の生成
    datas = []
    for row in rows:
        datas.append({"saleId": row[0], "productPhoto": row[-1], "sellingPrice": int(row[6]), "productName" :row[3], "listingStatus" : row[10] ,"deletionStatus":row[11]})
    sql_follow ="SELECT * from t_follow where accountId = %s"
    cur.execute(sql_follow, (accountId,))
    rows = cur.fetchall()
    #配列の生成
    follow = []
    for row in rows:
        follow.append({"accountId":row[1],"followerId":row[2],})
    follow_count = len(follow)
    
    sql_follower ="SELECT * from t_follow where followerId = %s"
    cur.execute(sql_follower, (accountId,))
    rows = cur.fetchall()
    #配列の生成
    follower = []
    for row in rows:
        follower.append({"accountId":row[1],"followerId":row[2],})
    follower_count = len(follower)  
    
        # フォロー中のユーザーIDを取得（フォロワー一覧）
    cur.execute("""
    SELECT t_account.accountId, t_account.accountName
    FROM t_account
    JOIN t_follow ON t_account.accountId = t_follow.accountId
    WHERE t_follow.followerId = %s
    """, (accountId,))
    rows = cur.fetchall()
    #配列の生成
    follows = []
    for row in rows:
        follows.append({"userId": row[0], "accountName": row[1]})
    
    # 被フォロー中のユーザーIDを取得（フォロワー一覧）
    cur.execute("""
    SELECT 
    f.followId,
    a1.accountId AS followedAccountId,
    a1.accountName AS followedAccountName,
    a2.accountId AS followerAccountId,
    a2.accountName AS followerAccountName
    FROM t_follow f
    JOIN t_account a1 ON f.accountId = a1.accountId
    JOIN t_account a2 ON f.followerId = a2.accountId
    WHERE a1.accountId = %s;
    """, (accountId,))
    rows = cur.fetchall()
    #配列の生成
    followers = []
    for row in rows:
        followers.append({"userId": row[3], "accountName": row[4]}) 
    
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    #curの終了
    cur.close()
    #conの終了
    con.close()
    
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("profile.html", aryData=aryData, datas=datas,point=point,accounts=accounts,follow=follow,follower=follower,follow_count=follow_count,follower_count=follower_count,follows=follows,followers=followers)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
    
    
# フォロー機能
@app.route('/follow', methods = ['POST'])
def follow():
    #ログイン中のユーザーの accountId を取得
    sessionId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if sessionId is None:
        return render_template('login.html')

    
    #入力画面から値の受け取り
    userId = request.form.get('userId')
    accountId = request.form.get('accountId')

    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    
    
    
    #実行したいSQLの作成
    sql = " SELECT * FROM t_follow WHERE accountId = %s AND followerId = %s "
    cur.execute(sql, (userId, accountId,))
    rows = cur.fetchall()
    
    
    if rows:
        pass
        
    else:
        #00001から順にPKを作成する
        cur.execute("SELECT MAX(followId) FROM t_follow")
        max_id = cur.fetchone()[0]
        if max_id:
            followId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
        else:
            followId = "00001"  # 初回は"00001"から始める
            
            
        #実行したいSQLの作成
        sql = """
        INSERT INTO t_follow 
        (followId, accountId, followerId)
        VALUES (%s, %s, %s)"""

        cur.execute(sql,[followId, userId, accountId])
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0    
    con.commit()
    #curの終了
    cur.close()
    #conの終了
    con.close()


    return redirect(url_for("profile", searchId=userId , point=point))



# フォロー解除機能
@app.route('/unfollow', methods = ['POST'], endpoint='unfollow')
def unfollow():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')


    #入力画面から値の受け取り
    userId = request.form.get('userId')


    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成
    
    
    
    #実行したいSQLの作成
    sql = " DELETE FROM t_follow WHERE accountId = %s AND followerId = %s "
    cur.execute(sql, (userId, accountId,))
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    con.commit()
        
    #curの終了
    cur.close()
    #conの終了
    con.close()


    return redirect(url_for("profile", searchId=userId , point=point))

# アイコン更新
@app.route('/update_icon')
def update_icon():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
    
    
    con = conn_db()
    cur = con.cursor()
    
    #実行したいSQLの作成
    sql = " SELECT * from t_account WHERE accountId = %s"
    cur.execute(sql, (accountId,))
    rows = cur.fetchall()
    #配列の生成
    account_datas = []
    for row in rows:
        account_datas.append({"icon": row[2]})
    
    # './static/' を削除（None チェックあり）
    #for account in account_datas:
    #    if account['icon']:  # None でないことを確認
    #        account['icon'] = account['icon'].replace('./static/', '')
    
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0  
    #curの終了
    cur.close()
    #conの終了
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("update_icon.html", aryData=aryData,point=point,account_datas=account_datas)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ


# アイコン更新処理
@app.route('/submit_icon', methods=['POST'])
def submit_icon():
    #ログイン中のユーザーの accountId を取得
    accountId = session.get("login_id")
    
    #セッションが無効だった場合にログイン画面へ遷移
    if accountId is None:
        return render_template('login.html')
    
    
    con = conn_db()
    cur = con.cursor()


    #実行したいSQLの作成
    sql = " SELECT * from t_account WHERE accountId = %s"
    cur.execute(sql, (accountId,))
    rows = cur.fetchall()
    
    #配列の生成
    account_datas = []
    
    for row in rows:
        account_datas.append({"icon": row[2]})
    
    # './static/' を削除（None チェックあり）
    for account in account_datas:
        if account['icon']:  # None でないことを確認
            account['icon'] = account['icon'].replace('./static/', '')

    
    # ファイルオブジェクトを取得
    file = request.files.get('upload1')

    # ファイルが選択されているか確認
    if file and file.filename:
        # ファイル名の拡張子を取得
        file_extension = file.filename.split('.')[-1].lower()

        # 拡張子が許可された形式かどうかをチェック
        if file_extension not in okImage:
            return render_template("update_icon.html", error_message="許可されていないファイル形式です。", account_datas=account_datas)

        else:
            random_string = generate_random_string()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # YYYYMMDDHHMMSS形式
            filename = f"{accountId}_{timestamp}_{random_string}_{file.filename}"
                
            # ファイル(パス)の設定
            path = os.path.join("./static/upload/", filename)
                        
            # ファイルの保存
            file.save(path)
            
            # データの挿入
            sql = """
                UPDATE t_account
                SET 
                    icon = %(path)s
                WHERE accountId = %(accountId)s
            """
            
            data = {
                'path': path,
                'accountId': accountId
            }
            
            cur.execute(sql, data)

    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0    
    # データベースの変更を確定
    con.commit()
    con.close()
    cur.close()
    

    # 成功時のリダイレクト
    return redirect(url_for("profile", searchId=accountId , point=point))

#DM表示
@app.route('/dm')
def dm():
    
    #ログイン中のユーザーの accountId を取得
    senderId = session.get("login_id")
    search_id = request.args.get('searchId')
    receiverId =  request.args.get('searchId')
    #セッションが無効だった場合にログイン画面へ遷移
    if senderId is None:
        return render_template('login.html')
    
    # メッセージ履歴の取得 (送信者と受信者両方)
    con = conn_db()
    cur = con.cursor()
    
    
    # SQL文
    sql = """
    SELECT * 
    FROM t_directMessage 
    WHERE 
        (
            (accountId = %s AND senderId = %s) 
            OR 
            (accountId = %s AND senderId = %s)
        ) 
        AND directMessageDeletionStatus = 0
    ORDER BY directSendDateTime ASC;"""

    #データベース接続してSQL文を実行
    cur.execute(sql, (receiverId, senderId, senderId, receiverId))
    rows = cur.fetchall()
    messages=[]
    # データを辞書で準備
    for row in rows:
        dm_datetime = row[5]  # 例: datetimeオブジェクトの場合
        formatted_dm_datetime = dm_datetime.strftime("%Y年%m月%d日 %H:%M:%S")
        messages.append({"receiveAccountId": row[1],"senderAccountId":row[2],"DMcontent":row[3],"DMMedia":row[4],"DMDateTime":formatted_dm_datetime})
    print(messages)
    
    sql = "SELECT accountName FROM t_account WHERE accountId = %s"
    cur.execute(sql, (receiverId,))
    rows = cur.fetchall()
    receiverAccountName = []
    for row in rows:
        receiverAccountName.append({"accountName":row[0],})
    print(receiverAccountName)
    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0
    
    con.close()
    cur.close()
    
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("dm.html", aryData=aryData ,point=point ,messages=messages ,receiverAccountName=receiverAccountName,search_id=search_id)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ



#DM送信
@app.route('/dm_send', methods=['POST'])
def dm_send():
    
    #ログイン中のユーザーの accountId を取得
    senderId = session.get("login_id")
    #セッションが無効だった場合にログイン画面へ遷移
    if senderId is None:
        return render_template('login.html')
    
    accountId = request.form.get('searchId')
    senderId = request.form.get('senderId')
    #file = request.files["directMessageAttachedMedia"]
            
    ## ファイル選択のチェック
    #if file.filename != "":
    #    random_string = generate_random_string()
    #    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # YYYYMMDDHHMMSS形式
    #    filename = f"{senderId}_{timestamp}_{random_string}_{file.filename}"
    #        
    #    # ファイル(パス)の設定
    #    path = os.path.join("./static/upload", filename)
    #                
    #    # ファイルの保存
    #    file.save(path)
    #    
    #else:
    #    path = None  # ファイルが選択されなかった場合
    
    
    con = conn_db()
    cur = con.cursor()
    
    #00001から順にアカウントIDを作成する
    cur.execute("SELECT MAX(directMessageId) FROM t_directMessage")
    max_id = cur.fetchone()[0]
    if max_id:
        directMessageId = f"{int(max_id) + 1:05}"  # 最大IDに1を足し、ゼロパディングで5桁に整形
    else:
        directMessageId = "00001"  # 初回は"00001"から始める
 
 
    #入力画面から値の受け取り
    directMessageContent = request.form.get('directMessageContent')
    #directMessageAttachedMedia = path


    # SQL文
    sql = """
        INSERT INTO t_directMessage (
            directMessageId, accountId, senderId, directMessageContent, directSendDateTime, directMessageDeletionStatus
        ) VALUES (
            %s, %s, %s, %s, %s, 0
        )
    """
 
    # データベース接続してSQL文を実行
    cur.execute(sql, (directMessageId,accountId,senderId,directMessageContent,datetime.now(),))
 
 
    #データ確定
    con.commit()
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0    
    con.close()
    cur.close()
    
    return redirect(url_for('dm',searchId=accountId , point=point))

#トップページ
@app.route('/top')
def search_top():
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成

    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0

    cur.close()
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("top.html", aryData=aryData ,point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ
    
#購入完了ページ
@app.route('/compPage')
def compPage():
    con = conn_db() #conn_db関数を呼び出して、DB接続
    cur = con.cursor() #SQL実行用cursorを作成

    accountId = session.get("login_id")
    sql = " SELECT points FROM t_account WHERE accountId = %s "
    cur.execute(sql, (accountId,))
    result = cur.fetchone()
    point = result[0] if result else 0

    cur.close()
    con.close()
    if "aryData" in session:
        aryData = json.loads(session["aryData"])  # JSONをリストに戻す
        return render_template("buy_comp.html", aryData=aryData,point=point)
    else:
        return render_template('login.html')  # ログインしていない場合はログインページへ

if __name__=="__main__":
    app.run(debug=True , port=2000)