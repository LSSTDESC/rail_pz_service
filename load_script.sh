pz-rail-service-admin init --reset
pz-rail-service-admin load algos-from-env
pz-rail-service-admin load catalog-tags-from-env
pz-rail-service-admin load model --name com_cam_trainz_base --path tests/temp_data/inputs/model_com_cam_trainz_base.pkl --algo-name TrainZEstimator --catalog-tag-name com_cam
pz-rail-service-admin load estimator --name com_cam_trainz_base --model-name com_cam_trainz_base
pz-rail-service-admin load dataset --name com_cam_test --path tests/temp_data/inputs/minimal_gold_test.hdf5 --catalog-tag-name com_cam
pz-rail-service-admin request create --dataset-name com_cam_test --estimator-name com_cam_trainz_base
pz-rail-service-admin request run --row-id 1
