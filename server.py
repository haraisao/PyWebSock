
import comm

if __name__ == '__main__' :
  reader = comm.HttpReader(None, "html")
  srv= comm.SocketServer(reader, "Web", "localhost", 8080)
  srv.start()

