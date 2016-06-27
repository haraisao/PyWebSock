
import comm

if __name__ == '__main__' :
  reader = comm.Html5Reader(None, "html")
  srv= comm.SocketServer(reader, "Web", "localhost", 8080)
  srv.start()

