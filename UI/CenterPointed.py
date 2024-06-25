import cv2
import time
import numpy as np
from sklearn import linear_model


class CenterPointed():

    def __init__(self):
        super().__init__()
        # npdata = np.load('C:/Users/azc27/4Grade/Nystagmography/ND/npy/leftlabel.npy', allow_pickle=True)
        # ee = self.ellipse(npdata[0])

        # # img = np.zeros((240,240),np.uint8)
        # img = npdata[0]
        # cv2.ellipse(img, ee, 255, 3) 
        # # img_no_channel = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # numpy_horizontal_concat = np.concatenate((npdata[0], img), axis=1)
        # cv2.imshow('Numpy Horizontal Concat', numpy_horizontal_concat)
        # cv2.waitKey(0)

        # # 모든 윈도우를 닫습니다.
        # cv2.destroyAllWindows()    
    
    def numpy_reshape(self, image):
        reimg = np.reshape(image, (240,240))
        reimg = (reimg * 255).astype(np.uint8)
        return reimg

    def image_contours(self,image):
        image = self.numpy_reshape(image)
        ret, imthres = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV)
        contours, hier = cv2.findContours(imthres, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours[1]
    
    def ellipse(self, image):
        image = self.image_contours(image)
        ellipse = cv2.fitEllipse(image)
        return ellipse
    
    def HoughCircle(self, image):
        img = self.numpy_reshape(image)
        blurred = cv2.GaussianBlur(img, (9, 9), 0)
        circles = cv2.HoughCircles(blurred,cv2.HOUGH_GRADIENT, 1, 10, param1 = 70, param2 = 30, minRadius = 0, maxRadius = 0)
        if circles is not None:
            circles = np.round(circles[0, :]).astype("float")
            return (circles[0][0], circles[0][1], circles[0][2])
        

    def fit_ransac(self, data, sample_num=10):
        image = self.image_contours(data)
        
        while True:
            time.sleep(0.001)
    
            sample = np.random.choice(len(image), sample_num, replace=False)
            # print(sample)
            xs = image[sample][:,:,0].reshape(-1,1)
            ys = image[sample][:,:,1].reshape(-1,1)

            ransac = linear_model.RANSACRegressor(stop_n_inliers=6)
            ransac.fit(xs, ys)
            inlier_mask = ransac.inlier_mask_

            if np.sum(inlier_mask) < 5:
                continue
            else:
                break        


        xmask = np.ravel(xs[inlier_mask], order='C')
        ymask = np.ravel(ys[inlier_mask], order='C')
        print(xmask, ymask)
        ran_sample = np.array([[x,y] for (x,y) in zip(xmask, ymask)])

        return cv2.fitEllipse(ran_sample)
    
    


CenterPointed()