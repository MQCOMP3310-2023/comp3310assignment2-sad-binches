from project import create_app

if __name__ == '__main__':
  app = create_app()
  app.run(host='0.0.0.0', port=8000, debug=False, ssl_context='adhoc') # turned off debugger to remove rce exploit with werkzeug debugger
  # added ssl context adhoc so application can be run over https
